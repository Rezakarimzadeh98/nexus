# Risk register (v1.1)

| ID | Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- | --- |
| R1 | Prompt/LLM assist misuse | Med | Med | LLM behind interfaces; baselines first |
| R2 | Tenant data bleed | Low | High | Tenant tables + audit; expand FK isolation |
| R3 | Secret leakage in CI/charts | Med | High | ExternalSecrets; no keys in values.yaml |
| R4 | Queue backlog / SLO miss | Med | Med | `/v1/metrics`, horizontal workers |
| R5 | Harmful operational use | Med | High | Product non-goals; ToS; defense adapter analytical-only |
| R6 | Supply-chain compromise | Low | High | SBOM in CI; pin images; signed releases (roadmap) |
