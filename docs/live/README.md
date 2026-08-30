# Live public snapshot

`status.json` is refreshed by the **Live ingest** GitHub Action (every 6 hours + manual dispatch).

The public demo site is published to GitHub Pages from `dashboard/index.html` + this snapshot.

Self-host the API:

```bash
pip install -e ".[api]"
uvicorn api.app:app --reload --port 8080
```
