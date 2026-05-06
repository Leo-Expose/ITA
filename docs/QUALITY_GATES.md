# Quality Gates

Release must satisfy all gates below:

## Trading Realism Gates (Net-of-Cost)
- Any metric used for tuning/calibration must prefer **net-of-cost** returns where available:
  - `paper_trades.pnl_5d_net_pct` (fallback: `pnl_5d_pct`)
  - `shadow_trades.pnl_5d_net_pct` (fallback: `pnl_5d_pct`)
- Cost model knob: `DEFAULT_CONFIG.estimated_round_trip_cost_bps` (conservative all-in drag).

## Unit Gates
- `tests/test_tool_validation.py`
- `tests/test_rule_based_analysis.py`
- `tests/test_recommender_free_tier.py`
- `tests/test_interface_fallback.py`
- `tests/test_nse_error_contract.py`
- `tests/test_health_endpoint.py`

## Integration Gates
- Analyst tool-call flow does not crash on malformed args.
- NSE adapters return `DATA_UNAVAILABLE` contract for failed upstream fetches.
- Recommendation response always includes provenance fields:
  - `decision_source`
  - `free_tier_mode`
  - `trade_overlay` (manual execution sizing + SL/target; may be `{ok:false}` on error)

## Quality Gate (Safe Auto-Tuning)
When applying tuned/regime/bandit weights via API, support the optional guardrail:
- `require_holdout_pass=true` and `holdout_days=N` on:
  - `POST /api/signal-performance/apply`
  - `POST /api/signal-performance/regime-apply`
  - `POST /api/signal-performance/bandit-apply`
If enabled and gates fail, the apply call must be blocked with a diagnostic payload (`blocked: quality_gates_failed`).

## E2E Gates
- Run representative symbols: `RELIANCE`, `TCS`, `HDFCBANK`.
- Validate market-closed date behavior (holiday/weekend dates).
- Optional network-backed smoke: `RUN_E2E=1 pytest -q tests/test_e2e_smoke.py`

## Performance and Cost Gates
- Track median recommendation latency for `nifty100`.
- Track analysis token usage under free-tier mode.
- Alert when degraded mode is active via `/api/health`.
- Run benchmark script: `python3 scripts/benchmark_free_tier.py`

## Offline Evaluation Gates (Walk-forward)
- Walk-forward evaluation endpoints exist and return JSON:
  - `POST /api/eval/walkforward`
  - `GET /api/eval/walkforward/{run_id}`
- Eval results are persisted in SQLite (`eval_runs` table).

## Runtime Smoke Gates
- `python3 scripts/smoke_checks.py`
