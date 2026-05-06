## Frontend (Next.js 16 Trading Terminal)

This directory contains the web UI for the Indian Market Trading Agent.

### What the UI is for (single-user workflow)
- Use **Today** and **Top Picks** to get trade ideas.
- Each pick surfaces a deterministic **manual execution overlay** (size ₹, shares, SL, target, risk).
- Use **Simulation** and **Shadow Trades** to measure whether your filtering helps or hurts.
- Use **Signal Performance** to tune the recommender weights (optionally guarded by quality gates).

## Getting Started

First, install deps and run the dev server:

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

### Backend dependency

By default the frontend calls the backend at `http://localhost:8000`.
Override with:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

### Key pages
- `src/app/page.tsx`: Dashboard (Today)
- `src/app/recommendations/page.tsx`: Top Picks / Recommendations
- `src/components/dashboard/TodayPicks.tsx`: Top picks widget shown on dashboard

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy

This repo is primarily designed to run locally (single-user). If you deploy it, ensure the backend is reachable and locked down appropriately (API keys are stored locally in SQLite on the backend host).
