# On-call runbook (reference)

## Alerts

| Signal | Source | Action |
| --- | --- | --- |
| `slo_ok=false` | `GET /v1/metrics` | Check worker replicas; inspect failed jobs |
| API 5xx spike | Ingress / APM | Roll back chart; check Postgres |
| Queue depth high | `jobs_queued` | Scale `worker` deployment |

## Common fixes

```bash
# Drain one job locally
python -m nexus_core.cli worker --once

# Apply retention
python -m nexus_core.cli retain --tenant-slug acme

# DB migrate
alembic upgrade head
```

Escalate using [SUPPORT.md](../../SUPPORT.md) for contracted customers.
