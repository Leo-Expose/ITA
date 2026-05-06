"""Lightweight in-process metrics for degraded-mode visibility."""

from __future__ import annotations

from threading import Lock

_lock = Lock()
_counters: dict[str, int] = {
    "fallback_activations": 0,
    "upstream_failures": 0,
    "recommender_runs": 0,
}


def incr(metric: str, value: int = 1) -> None:
    with _lock:
        _counters[metric] = _counters.get(metric, 0) + value


def get_counters() -> dict[str, int]:
    with _lock:
        return dict(_counters)
