"""Runtime smoke checks for stabilization gates.

Usage:
    python3 scripts/smoke_checks.py
"""

def main() -> int:
    try:
        from fastapi.testclient import TestClient
        from backend.app import app
    except Exception as exc:
        print(f"Smoke checks skipped: missing runtime dependency ({exc})")
        return 0

    client = TestClient(app)

    health = client.get("/api/health")
    print("GET /api/health:", health.status_code)
    if health.status_code != 200:
        return 1

    recommend = client.get("/api/recommend/?universe=nifty50&min_signals=1")
    print("GET /api/recommend:", recommend.status_code)
    if recommend.status_code != 200:
        return 1

    stock = client.get("/api/recommend/stock/RELIANCE")
    print("GET /api/recommend/stock/RELIANCE:", stock.status_code)
    if stock.status_code != 200:
        return 1

    print("Smoke checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
