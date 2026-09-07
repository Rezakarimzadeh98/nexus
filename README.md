# NEXUS — Enterprise Intelligence for FX & Market Signals

NEXUS is an enterprise-grade market intelligence platform designed for live FX monitoring, technical analysis, sentiment-aware decision support, and operational risk visibility in a single interface.

It combines secure API access, role-based governance, real market data, signal engine logic, and a responsive dashboard built for analysts, operators, and portfolio teams.

## Live Preview

- Local app: http://localhost:8080
- Public online tunnel: https://tidy-jeans-push.loca.lt
- GitHub repo: https://github.com/Rezakarimzadeh98/nexus
- GitHub Pages landing: https://rezakarimzadeh98.github.io/nexus/

Current tunnel status: validated on 2026-09-07 via `/api/health`.

## Why NEXUS

- Real-time FX analytics with live market data
- Mixed signal stack: technical, macro, news-driven, and forecasted
- Enterprise-ready controls: auth, roles, audit, rate limiting
- Operational dashboard for analysts and decision makers
- Designed for professional presentation and business reporting

## Demo Media

Project-owned visuals (no stock placeholders):

![NEXUS dashboard preview](docs/media/nexus-dashboard.svg)
![NEXUS decision pipeline](docs/media/nexus-flow.svg)
![NEXUS live refresh loop](docs/media/nexus-live-loop.svg)

## Product Walkthrough

- Start the platform: `npm start` then open `http://localhost:8080`
- Run full analysis: use `Run Full Analysis` in the dashboard
- Enable resilient live mode: set `Auto Refresh` to 30s/60s/120s/300s
- Validate governance: load `/api/admin/me` and `/api/admin/audit` via dashboard controls
- Operator shortcuts: `Alt+R` run full analysis, `Alt+A` load audit events

## Core Capabilities

- Multi-pair FX analytics by base and target currencies
- Technical indicator engine: SMA, EMA, WMA, RSI, Stochastic RSI, MACD, Bollinger, ROC, Momentum, Z-Score, ATR, ADX, CCI
- OHLC-driven market validation using Yahoo Finance and Stooq fallback
- Forecast modeling with Holt trend estimation and confidence bands
- News sentiment analysis for market tone and narrative pressure
- Composite decision score with actionable verdicts
- Manual record ingestion for analyst-approved overrides
- Role-based API access and audit logging for governance

## Architecture

- App entry: [src/app.js](src/app.js)
- Server bootstrap: [src/server.js](src/server.js)
- Dashboard UI: [public/index.html](public/index.html)
- Frontend logic: [public/app.js](public/app.js)
- Indicator engine: [src/services/indicatorEngine.js](src/services/indicatorEngine.js)
- Forecast engine: [src/services/forecastService.js](src/services/forecastService.js)
- Decision engine: [src/services/decisionService.js](src/services/decisionService.js)
- News engine: [src/services/newsAnalysisService.js](src/services/newsAnalysisService.js)
- Security middleware: [src/middleware/auth.js](src/middleware/auth.js), [src/middleware/rateLimit.js](src/middleware/rateLimit.js), [src/middleware/audit.js](src/middleware/audit.js)

## Data Sources

- FX rates: https://api.frankfurter.app
- OHLC: Yahoo Finance Chart API (primary), Stooq (fallback)
- News feed: Google News RSS

## Security & Governance

- JWT-like API key protection on all protected routes
- Roles:
  - viewer: read only
  - analyst: read + manual writes
  - admin: full access + audit visibility
- Request rate limiting per IP + API key
- Audit trail for operational oversight

Default development keys:

- nexus-viewer-2026
- nexus-analyst-2026
- nexus-admin-2026

## API Surface

- GET /api/health
- GET /api/fx/timeseries?base=USD&targets=EUR,GBP,JPY&days=30
- GET /api/analytics/overview?base=USD&targets=EUR,GBP,JPY&days=180
- GET /api/forecast/overview?base=USD&targets=EUR,GBP,JPY&days=180&horizon=7
- GET /api/news/analyze?query=forex%20market&max=10
- GET /api/decision/score?base=USD&targets=EUR,GBP,JPY&days=180&horizon=7&newsQuery=forex%20market&newsMax=10
- POST /api/manual-records
- GET /api/admin/me
- GET /api/admin/audit?limit=50

## Full Indicator Set

- SMA 5, 10, 20, 50
- EMA 9, 21, 50
- WMA 20
- RSI 14
- Stochastic RSI 14
- MACD 12, 26, 9
- Bollinger Bands 20, 2
- ROC 12
- Momentum 10
- StdDev 20
- Z-Score 20
- Support & resistance banding
- Sharpe-like return factor
- Composite technical signal score 0-100
- ATR14, ADX14, CCI20, Stochastic K/D

## Quick Start

```bash
npm install
npm start
```

Then open:

```text
http://localhost:8080
```

## Verified Runtime Snapshot

The current implementation was validated with live API calls and returned:

- HEALTH=True
- ANALYTICS_RECORDS=190
- FORECAST_ITEMS=3
- NEWS_ITEMS=0 (depending on market source availability)
- DECISION_VERDICT=neutral
- DECISION_COMPOSITE≈44.53

## Production-Ready Positioning

This project is structured as an enterprise intelligence system with:

- Real-time ingestion and analytics workflows
- Forecast and sentiment-enriched decisioning
- UI-level operational controls (full analysis orchestration + auto refresh)
- Governance primitives (auth, role boundaries, rate limits, audit events)
- Presentation assets suitable for executive and technical audiences

## Repository Status

- GitHub repo: active and aligned to the NEXUS project
- Live version: online tunnel available
- Presentation layer: updated for enterprise clarity
- Data and analytics: operational and live-validated
