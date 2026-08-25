# Threat Model

## Scope and trust boundaries

The platform is a high-value security system. Its principal boundaries are the public browser, API, PostgreSQL, background collectors, the secret provider, and customer AWS accounts reached through STS AssumeRole. AWS event content is untrusted input.

## Threats and mitigations

| Threat | Primary mitigations | Residual work |
| --- | --- | --- |
| Stolen administrator password | Slow salted password hashes, expiring tokens, active-user checks, audit logs | Add MFA and managed identity for production |
| AWS credential exposure | Prefer role ARN and temporary STS credentials; response schemas omit external IDs and secrets; logs do not include request bodies | Use a managed secret provider for external IDs |
| Authorization bypass | Backend role dependencies protect account and AWS operations; viewer mutations return 403 | Add policy-based authorization tests for every admin route |
| Cross-account data leakage | Account IDs are persisted on resources and ingestion checkpoints | Add tenant/organization ownership before multi-tenant commercial use |
| SSRF | AWS destinations are created by the SDK, not user-provided URLs | Apply egress controls in production |
| Injection | Pydantic validation and SQLAlchemy parameterization | Add a WAF and continuous dependency scanning |
| Session theft | Short JWT expiry and TLS at ingress | Move browser authentication to Secure HttpOnly cookies with CSRF tokens |
| Excessive IAM privilege | Customer role template contains read-only named actions and an ExternalId condition | Review permissions whenever collectors expand |
| Misconfigured CORS | Explicit configuration and same-origin deployment | Restrict origins to the production hostname |
| Secret leakage through logs | Structured logging excludes request bodies and authorization headers | Add automated redaction tests |
| Malicious AWS event content | Normalize and validate before detection; React escapes rendered values | Add size limits and quarantine malformed events |
| Database compromise | Password hashes and no long-lived AWS access keys in account records | Encrypt external IDs and backups with managed KMS |

## Security invariants

- Only administrators may create, change, validate, enable, disable, or delete cloud accounts.
- AWS secret access keys are never returned by an API or delivered to frontend code.
- Account access uses STS AssumeRole and short-lived credentials by default.
- Every sensitive state-changing API request is audited without its body or token.
- Production traffic terminates TLS before reaching the application.
