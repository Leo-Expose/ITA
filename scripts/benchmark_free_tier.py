"""Simple benchmark for free-tier vs baseline recommender runtime."""

from __future__ import annotations

import statistics
import time

def _bench_once(universe: str = "nifty100") -> float:
    from backend.recommender import recommend
    t0 = time.perf_counter()
    recommend(universe=universe, min_signals=2, apply_market_bias=False, apply_event_filter=False, apply_concentration_check=False)
    return time.perf_counter() - t0


def run(mode_name: str, free_tier_mode: bool, n: int = 3) -> dict:
    from tradingagents.dataflows.config import get_config, set_config
    cfg = get_config()
    set_config({**cfg, "free_tier_mode": free_tier_mode})
    vals = [_bench_once() for _ in range(n)]
    return {
        "mode": mode_name,
        "runs": n,
        "median_sec": round(statistics.median(vals), 2),
        "p95_sec": round(max(vals), 2),
    }


def main() -> int:
    try:
        import yfinance  # noqa: F401
    except Exception as exc:
        print(f"Benchmark skipped: missing dependency ({exc})")
        return 0

    free = run("free_tier", True)
    baseline = run("baseline", False)
    print(free)
    print(baseline)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
