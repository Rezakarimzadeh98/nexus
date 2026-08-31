# PII handling policy

1. Prefer public / licensed sources; do not ingest known PII fields unless contractually required.
2. Before logging request bodies or exporting dumps, run `redact_mapping` / `redact_text`.
3. Tenant admins set retention via `retention_days`; use `nexus retain`.
4. Access to audit logs is an admin action and must itself be audited.
5. Contact the maintainer for DSAR / deletion workflows in enterprise contracts.
