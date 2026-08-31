# Security Policy

## Reporting

Please do not open public issues for vulnerabilities. Use a private GitHub security advisory or contact the maintainer.

## Scope

In-scope: auth flaws on write paths (`NEXUS_API_KEY` / Bearer), injection, data leakage across tenants (enterprise), provenance tampering, model/pipeline integrity.

Write routes under `/v1/jobs/*` require `Authorization: Bearer <NEXUS_API_KEY>` or `X-API-Key` when the key is configured. Public GET routes remain open for the live demo.

Out of scope: using NEXUS analytical outputs for real-world harm; that is a policy violation, not a “feature request.”