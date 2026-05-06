# Degraded Mode Runbook

## Purpose
Explain how to detect and respond when the system is operating in degraded mode.

## Detection
- Check `GET /api/health`.
- Key fields:
  - `status`
  - `degraded_reasons`
  - `stale_data_flags`
  - `metrics.fallback_activations`
  - `metrics.upstream_failures`

## Common Triggers
- Missing major LLM credentials.
- Stale or unavailable FII/DII cache.
- High upstream failure and fallback counts from NSE/vendor calls.
- Yahoo/yfinance intermittently returning 404s for some symbols (should be handled as “skip stock”, not crash).

## Operator Actions
1. Verify provider credentials in Settings.
2. Refresh data caches and re-run smoke checks:
   - `PYTHONPATH=. python3 scripts/smoke_checks.py`
3. If upstream instability continues:
   - keep `free_tier_mode` enabled
   - reduce high-cost analysis usage
   - rely on deterministic recommendation workflow
4. If many tickers fail from yfinance:
   - switch universes (`nifty50` tends to be most stable)
   - reduce `min_signals` temporarily to avoid an empty day when data is partial

## Recovery Criteria
- `status: ok` on `/api/health`.
- No stale data flags.
- Upstream failures stop increasing rapidly across consecutive checks.
