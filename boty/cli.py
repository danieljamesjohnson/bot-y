"""Command line entry point.

    boty check   -- one pass, print a table, exit (good for cron and for eyeballing)
    boty watch   -- loop forever, notify on transitions (good for systemd)
"""

from __future__ import annotations

import argparse
import logging
import random
import sys
import time

from .config import Config
from .models import Availability
from .monitor import State, run_once
from .notify import send_health_warning, send_restock
from .retailers import check_bestbuy_api, check_html
from .status import write as write_status

SYMBOL = {
    Availability.IN_STOCK: "\033[32m●\033[0m",
    Availability.OUT_OF_STOCK: "\033[90m○\033[0m",
    Availability.UNKNOWN: "\033[33m?\033[0m",
}


def _make_checker(cfg: Config):
    def check(watch):
        if watch.retailer == "bestbuy" and cfg.bestbuy_api_key:
            return check_bestbuy_api(watch, cfg.bestbuy_api_key)
        return check_html(watch, first_party_only=cfg.first_party_only)

    return check


def _report(results, health) -> None:
    for r in results:
        price = f"${r.price:>8.2f}" if r.price is not None else " " * 9
        tag = " [control]" if r.watch.control else ""
        print(f"  {SYMBOL[r.availability]} {r.watch.retailer:<9} {r.watch.name[:30]:<30}{price}  {r.detail[:56]}{tag}")

    for h in health:
        if not h.ok:
            print(f"\n  \033[33m! {h.retailer}: {h.reason}\033[0m")
            for c in h.failing_controls:
                print(f"      {c}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="boty", description="Restock monitor that tells you when it breaks.")
    ap.add_argument("command", choices=["check", "watch"])
    ap.add_argument("-c", "--config", default="config/products.yaml")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)-7s %(message)s",
    )

    cfg = Config.load(args.config)
    if not cfg.watches:
        print("no watches configured", file=sys.stderr)
        return 2

    checker = _make_checker(cfg)
    state = State.load(cfg.state_path)

    if args.command == "check":
        results, health, alerts = run_once(cfg.watches, checker, state)
        _report(results, health)
        write_status(cfg.status_path, results, health)
        if alerts:
            print(f"\n  {len(alerts)} alertable transition(s)")
        return 0

    print(f"watching {len(cfg.watches)} product(s) every ~{cfg.interval_seconds}s. ctrl-c to stop.")
    warned: set[str] = set()
    while True:
        try:
            results, health, alerts = run_once(cfg.watches, checker, state)
            write_status(cfg.status_path, results, health)
            if alerts:
                send_restock(cfg.notify_urls, alerts)

            # Warn once per retailer per failure episode, not every cycle.
            unhealthy = [h for h in health if not h.ok]
            fresh = [h for h in unhealthy if h.retailer not in warned]
            if fresh:
                send_health_warning(cfg.notify_urls, fresh)
            warned = {h.retailer for h in unhealthy}
        except Exception:
            logging.exception("check cycle failed; continuing")

        # Jitter so we do not hammer on a fixed cadence, which is itself a signal.
        time.sleep(cfg.interval_seconds * random.uniform(0.85, 1.15))


if __name__ == "__main__":
    raise SystemExit(main())
