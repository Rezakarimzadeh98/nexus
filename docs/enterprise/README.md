# Enterprise deployment

Sellable packaging for the same NEXUS core (Phase 12).

## Tenancy & identity

- Tables: `tenants`, `memberships`, `audit_events`, `jobs` (Alembic `0005_tenancy`)
- API: `/v1/tenants`, `/v1/audit`, `/v1/jobs/enqueue`, `/v1/auth/oidc`
- Admin console: `/admin/`
- Roles: `viewer` | `operator` | `admin` (`nexus_core.enterprise.rbac`)
- Isolation: `tenant_id` FK on observations/signals/forecasts + memberships/audit/jobs

### SSO (OIDC)

1. Set `NEXUS_OIDC_ISSUER` to your IdP realm.
2. For demo HS256 validation set `NEXUS_OIDC_CLIENT_SECRET` (+ optional `NEXUS_OIDC_AUDIENCE`).
3. Production: set issuer (JWKS/RS256 via PyJWT) or terminate OIDC at the gateway.
4. SAML: front with a broker (Keycloak / Auth0) that issues OIDC to NEXUS.
5. Demo-only: `NEXUS_OIDC_CLIENT_SECRET` enables HS256 validation.

## Reliability & scale

- DB-backed queue (`jobs`) + `nexus worker` horizontal processes (`SKIP LOCKED`)
- Compose: `worker` service; Redis profile for cache
- Metrics: `GET /v1/metrics` (ingest success ratio vs `NEXUS_SLO_INGEST_SUCCESS_RATIO`)
- Retention: `nexus retain [--tenant-slug …]`
- Quotas: `tenants.monthly_ingest_quota` (enforcement hooks for gateways)

## Governance

- Data residency: `tenants.region`
- PII: `nexus_core.enterprise.pii.redact_*` + [PII policy](PII.md)
- Model card / risk: [MODEL_CARD.md](MODEL_CARD.md), [RISK_REGISTER.md](RISK_REGISTER.md)

## Packaging

- Helm: `infrastructure/helm/nexus`
- SLA: [SLA.md](SLA.md)
- Support: [../../SUPPORT.md](../../SUPPORT.md)
- Import: `nexus import-observations --path file.json [--tenant-slug acme]`

## Security

- Prefer JWKS/RS256 with `NEXUS_OIDC_ISSUER` (and optional `NEXUS_OIDC_JWKS_URI`)
- Fact tables carry nullable `tenant_id` FK (`observations`, `signals`, `forecasts`)
- Monthly ingest quotas enforced on persist
- Secrets via env / external secret stores (`NEXUS_SECRETS_BACKEND=env`)
- SBOM in CI; releases: `.github/workflows/release.yml` (SBOM + provenance attestations)
- Checklist: [PENTEST.md](PENTEST.md)
