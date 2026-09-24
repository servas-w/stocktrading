"""Persistent state between daily runs: tracked tickers and already-sent news."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field

SEEN_TTL_SECONDS = 14 * 24 * 3600


@dataclass
class State:
    # Tickers this bot added to the watchlist. Only these are ever removed, so
    # symbols you add by hand are left alone.
    tracked: set[str] = field(default_factory=set)
    # news/filing id -> unix time first seen (for de-duplication)
    seen: dict[str, float] = field(default_factory=dict)
    last_run: float | None = None

    @classmethod
    def load(cls, path: str) -> "State":
        if not os.path.exists(path):
            return cls()
        with open(path) as f:
            raw = json.load(f)
        return cls(
            tracked=set(raw.get("tracked", [])),
            seen=dict(raw.get("seen", {})),
            last_run=raw.get("last_run"),
        )

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(
                {"tracked": sorted(self.tracked), "seen": self.seen, "last_run": self.last_run},
                f,
                indent=2,
            )
        os.replace(tmp, path)

    def prune_seen(self, now: float | None = None) -> None:
        cutoff = (now or time.time()) - SEEN_TTL_SECONDS
        self.seen = {k: v for k, v in self.seen.items() if v >= cutoff}


@dataclass(frozen=True)
class PositionDiff:
    opened: set[str]
    closed: set[str]
    held: set[str]


def diff_positions(previous: set[str], current: set[str]) -> PositionDiff:
    return PositionDiff(opened=current - previous, closed=previous - current, held=current)
