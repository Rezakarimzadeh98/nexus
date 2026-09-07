# Security Policy

## Reporting a Vulnerability

Please report security issues privately before opening public issues.
Include:

- Affected endpoint/file
- Reproduction steps
- Expected vs actual behavior
- Potential impact

## Scope

- Authentication and API key handling
- Rate limiting and abuse controls
- Injection and input validation
- Dependency vulnerabilities
- Runtime/network exposure issues

## Best Practices in This Repo

- Protected routes require API key.
- Role-based access checks for admin routes.
- Rate limiting is enabled.
- Audit logging for API operations.
- Timeouts and retries used for upstream calls.

## Disclosure Timeline

- Acknowledge report within 72 hours.
- Initial assessment within 7 days.
- Mitigation plan and patch ETA after triage.
