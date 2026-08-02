"""Config loading.

Adding a product is editing a YAML file. That is the whole bar, and it is
the main thing that makes bot-y different from the tools it replaces —
streetmerchant, for instance, requires editing two TypeScript union types,
a per-series price map, and a store file to add a single SKU.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .models import Watch

_ENV_RE = re.compile(r"\$\{([A-Z0-9_]+)\}")


def _expand(value: Any) -> Any:
    """Expand ${VAR} from the environment so secrets stay out of the file."""
    if isinstance(value, str):
        return _ENV_RE.sub(lambda m: os.environ.get(m.group(1), ""), value)
    if isinstance(value, list):
        return [_expand(v) for v in value]
    if isinstance(value, dict):
        return {k: _expand(v) for k, v in value.items()}
    return value


@dataclass
class Config:
    watches: list[Watch]
    notify_urls: list[str] = field(default_factory=list)
    bestbuy_api_key: str = ""
    first_party_only: bool = True
    interval_seconds: int = 300
    state_path: Path = Path("state.json")
    #: Snapshot for the dashboard. Written every cycle; served as a static file.
    status_path: Path = Path("served/boty/status.json")

    @classmethod
    def load(cls, path: str | Path) -> Config:
        raw = _expand(yaml.safe_load(Path(path).read_text()) or {})
        settings = raw.get("settings") or {}

        watches: list[Watch] = []
        for entry in raw.get("watches") or []:
            watches.append(
                Watch(
                    name=entry["name"],
                    retailer=entry["retailer"],
                    target=str(entry["target"]),
                    max_price=entry.get("max_price"),
                    control=bool(entry.get("control", False)),
                )
            )

        return cls(
            watches=watches,
            notify_urls=[u for u in (raw.get("notify") or []) if u],
            bestbuy_api_key=settings.get("bestbuy_api_key", ""),
            first_party_only=bool(settings.get("first_party_only", True)),
            interval_seconds=int(settings.get("interval_seconds", 300)),
            state_path=Path(settings.get("state_path", "state.json")),
            status_path=Path(settings.get("status_path", "served/boty/status.json")),
        )
