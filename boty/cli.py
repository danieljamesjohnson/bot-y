"""Command line entry point.

    boty check           -- one pass, print a table, exit (good for cron and for eyeballing)
    boty watch           -- loop forever, notify on transitions (good for systemd)
    boty capture-fixture -- freeze a live retailer page as an offline test fixture
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


def _capture_fixture(args) -> int:
    """Freeze one live page as a fixture, or refuse and say why.

    A blocked fetch must never become a file on disk: a CAPTCHA interstitial
    saved under a product's name would make the whole test suite assert against
    a bot wall while looking perfectly green.
    """
    from .fetch import Blocked, FetchError
    from .fixtures import capture, meta_path

    try:
        path = capture(args.retailer, args.name, args.url, note=args.note)
    except Blocked as exc:
        print(f"blocked: {exc}", file=sys.stderr)
        print("refusing to save a challenge page as a fixture", file=sys.stderr)
        return 1
    except FetchError as exc:
        print(f"fetch failed: {exc}", file=sys.stderr)
        return 1

    print(f"wrote {path} ({path.stat().st_size:,} bytes)")
    print(f"      {meta_path(args.retailer, args.name)}")
    if not args.note:
        print(
            "warning: no --note recorded — a future reader cannot tell what "
            "stock state this page represented",
            file=sys.stderr,
        )
    return 0


def _add_shared(p: argparse.ArgumentParser) -> None:
    p.add_argument("-c", "--config", default="config/products.yaml")
    p.add_argument("-v", "--verbose", action="store_true")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="boty", description="Restock monitor that tells you when it breaks.")
    sub = ap.add_subparsers(dest="command", required=True)

    _add_shared(sub.add_parser("check", help="one pass, print a table, exit"))
    _add_shared(sub.add_parser("watch", help="loop forever, notify on transitions"))

    cap = sub.add_parser(
        "capture-fixture",
        help="save a live retailer page as an offline test fixture",
        description=(
            "Fetch a live product page and freeze it under tests/fixtures/ with "
            "capture metadata. Needs no config file."
        ),
    )
    cap.add_argument("retailer", help="retailer key, e.g. gamestop")
    cap.add_argument("name", help="fixture name, e.g. goplusplus")
    cap.add_argument("url", help="product URL to capture")
    cap.add_argument(
        "--note",
        default="",
        help="what stock state this page represented at capture time",
    )
    cap.add_argument("-v", "--verbose", action="store_true")

    args = ap.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)-7s %(message)s",
    )

    # Capturing a fixture is a standalone tool: it takes a URL directly and has
    # nothing to say about watches, so it must not require a config file.
    if args.command == "capture-fixture":
        return _capture_fixture(args)

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
