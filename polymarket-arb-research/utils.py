from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from statistics import median
from typing import Iterable


UTC = timezone.utc


def ensure_utc(dt: datetime) -> datetime:
    """Normalize datetime to timezone-aware UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def utc_now() -> datetime:
    return datetime.now(UTC)


def to_iso(dt: datetime | None) -> str | None:
    """Stable ISO-8601 format with `Z` suffix and millisecond precision."""
    if dt is None:
        return None
    return ensure_utc(dt).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def parse_maybe_ts(raw: str | None) -> datetime | None:
    if not raw:
        return None
    text = raw.strip().replace("Z", "+00:00")
    return ensure_utc(datetime.fromisoformat(text))


def from_unix_ms(ms: int | float) -> datetime:
    return datetime.fromtimestamp(float(ms) / 1000, tz=UTC)


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def json_dumps(data: dict) -> str:
    return json.dumps(data, separators=(",", ":"), sort_keys=True)


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, int(round(pct * (len(ordered) - 1)))))
    return ordered[idx]


def safe_mean(values: Iterable[float]) -> float:
    vals = list(values)
    return sum(vals) / len(vals) if vals else 0.0


def safe_median(values: list[float]) -> float:
    return median(values) if values else 0.0
