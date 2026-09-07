# Nexus Enterprise FX Analytics

پلتفرم تحلیل و پیش بینی بازار ارز با داده واقعی، معماری سرویس محور، امنیت نقش محور و داشبورد عملیاتی.

## Live Preview

- Local Web URL: http://localhost:8080
- Main Dashboard: http://localhost:8080

## Demo Media

![Nexus Demo GIF](https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExdXRmbTJjOWRscXQ1M2NmdXBrb2Q0a2NldGU5N2dwb3NwZnF0d2M5dSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/coxQHKASG60HrHtvkt/giphy.gif)

![Nexus Dashboard Preview](https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=1400&q=80)

## Project Summary

- Real-time currency analytics با داده واقعی
- Technical + OHLC indicators
- News sentiment analysis
- Time-series forecasting با confidence interval
- Composite decision scoring
- API security, role-based access, audit logging

## Data Sources

- FX Rates: https://api.frankfurter.app
- Reference: ECB rates
- OHLC: Yahoo Finance Chart API (primary), Stooq (fallback)
- News Feed: Google News RSS

## Enterprise Architecture

- Backend App: [src/app.js](src/app.js)
- Server Entry: [src/server.js](src/server.js)
- Public Dashboard: [public/index.html](public/index.html)
- Frontend Logic: [public/app.js](public/app.js)
- Technical Engine: [src/services/indicatorEngine.js](src/services/indicatorEngine.js)
- Forecast Engine: [src/services/forecastService.js](src/services/forecastService.js)
- Decision Engine: [src/services/decisionService.js](src/services/decisionService.js)
- News Engine: [src/services/newsAnalysisService.js](src/services/newsAnalysisService.js)
- Security Middleware: [src/middleware/auth.js](src/middleware/auth.js), [src/middleware/rateLimit.js](src/middleware/rateLimit.js), [src/middleware/audit.js](src/middleware/audit.js)

## Feature Matrix

- Multi-asset pair analytics by base/targets/days
- Full technical panel (close-series indicators)
- OHLC indicators: ATR14, ADX14, CCI20, Stoch K/D
- Forecasting (Holt linear trend)
- Forecast quality metrics: MAE, RMSE, MAPE
- News sentiment scoring
- Composite score and verdict for action bias
- Manual record ingestion with validation
- Admin audit trail and role checks

## Full Indicator Set

- SMA: 5, 10, 20, 50
- EMA: 9, 21, 50
- WMA: 20
- RSI: 14
- Stoch RSI: 14
- MACD: 12, 26, 9
- Bollinger Bands: 20, 2
- ROC: 12
- Momentum: 10
- StdDev: 20
- Z-Score: 20
- Support and Resistance: rolling 20
- Sharpe-like return factor
- Composite technical signal score 0..100
- ATR14, ADX14, CCI20, Stochastic K/D

## Security and Governance

- API Key auth for all /api routes except /api/health
- Roles:
  - viewer: read-only
  - analyst: read + manual write
  - admin: full + audit access
- Rate limiting per IP + API key
- Audit log storage in [data/audit.log](data/audit.log)

Default dev API keys:

- nexus-viewer-2026
- nexus-analyst-2026
- nexus-admin-2026

## API Endpoints

- GET /api/health
- GET /api/fx/timeseries?base=USD&targets=EUR,GBP,JPY&days=30
- GET /api/analytics/overview?base=USD&targets=EUR,GBP,JPY&days=180
- GET /api/forecast/overview?base=USD&targets=EUR,GBP,JPY&days=180&horizon=7
- GET /api/news/analyze?query=forex%20market&max=10
- GET /api/decision/score?base=USD&targets=EUR,GBP,JPY&days=180&horizon=7&newsQuery=forex%20market&newsMax=10
- POST /api/manual-records
- GET /api/admin/me
- GET /api/admin/audit?limit=50

## Run

1. npm install
2. npm start
3. Open http://localhost:8080

## Verified Runtime Snapshot

- HEALTH=True
- ANALYTICS_RECORDS=373
- FORECAST_ITEMS=3
- NEWS_ITEMS=10
- DECISION_VERDICT=neutral
- DECISION_COMPOSITE=45.33
- OHLC sample indicators validated with non-zero values

## Repo Phase Status

Phase closed for repository presentation: README now includes live URL, demo GIF/image, full content structure, architecture summary, endpoint map, and operational readiness details.
