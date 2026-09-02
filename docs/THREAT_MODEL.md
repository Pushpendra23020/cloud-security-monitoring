# Threat Model

## Scope and trust boundaries

The platform is a high-value security system. Its principal boundaries are the public browser, API, PostgreSQL, background collectors, the secret provider, and customer AWS accounts reached through STS AssumeRole. AWS event content is untrusted input.

## Threats and mitigations

| Threat | Primary mitigations | Residual work |
| --- | --- | --- |
| Stolen administrator password | Slow salted password hashes, password complexity, configurable lockout, shared PostgreSQL rate limits, encrypted TOTP MFA, single-use recovery codes, OIDC and login audit records | Add native WebAuthn/passkeys and risk-based detection |
| AWS credential exposure | Prefer role ARN and temporary STS credentials; response schemas omit external IDs and secrets; logs do not include request bodies | Use a managed secret provider for external IDs |
| Authorization bypass | Session, membership and roles are reloaded from PostgreSQL; backend role dependencies protect account and AWS operations; viewer mutations return 403 | Add policy-based authorization tests for every admin route |
| Cross-tenant data leakage | Required organization ownership, scoped repositories, tenant-aware uniqueness, composite tenant foreign keys, membership-bound JWTs, forced PostgreSQL RLS, transaction-local tenant context, and adversarial database tests | Keep every new tenant table under the RLS migration checklist and use tenant-bound worker credentials |
| Wrong AWS account collection | The selected cloud account is resolved inside the tenant, its monitoring role is assumed, and the returned STS account ID must match before EC2 collection | Extend the same invariant to every collector and scheduled job |
| SSRF | AWS destinations are created by the SDK, not user-provided URLs | Apply egress controls in production |
| Injection | Pydantic validation and SQLAlchemy parameterization | Add a WAF and continuous dependency scanning |
| Session theft | Ten-minute in-memory access tokens, hashed rotating refresh tokens, Secure HttpOnly SameSite cookies, replay revocation, server-side session expiry, MFA and user-visible revocation | Add managed risk-based session detection and native WebAuthn |
| MFA bypass or replay | AES-GCM-protected TOTP seeds, one-time TOTP steps, row-locked single-use challenges, keyed-hash recovery codes, challenge rate limits and session revocation after MFA changes | Prefer passkeys or IdP-enforced phishing-resistant factors for privileged accounts |
| OIDC account takeover | Authorization code with PKCE, signed state, nonce, exact issuer/audience, JWKS verification, algorithm allowlist, pre-provisioning and optional domain allowlist | Monitor identity-provider risk signals and key rotation |
| Excessive IAM privilege | Customer role template contains read-only named actions and an ExternalId condition | Review permissions whenever collectors expand |
| Misconfigured CORS | Explicit configuration and same-origin deployment | Restrict origins to the production hostname |
| Secret leakage through logs | Structured logging excludes request bodies and authorization headers | Add automated redaction tests |
| Malicious AWS event content | Normalize and validate before detection; React escapes rendered values | Add size limits and quarantine malformed events |
| Lost or duplicated event processing | PostgreSQL durable persistence, tenant-scoped idempotency, leased `SKIP LOCKED` claims, retry backoff and dead-letter replay | Exercise disaster recovery and high-volume replay drills |
| Worker crash or stalled lease | Timestamped leases are recovered after a configurable timeout; final expired attempts move to dead-letter | Alert on queue age, retry growth and dead-letter count |
| Event archive tampering or deletion | Canonical SHA-256 envelopes, exclusive filesystem creation, S3 conditional writes, encryption and compliance Object Lock | Restrict S3 delete/object-lock permissions to a separate break-glass role |
| Database compromise | Password hashes and no long-lived AWS access keys in account records | Encrypt external IDs and backups with managed KMS |

## Security invariants

- Only organization administrators may create, change, validate, enable, disable, or delete that organization's cloud accounts.
- Every customer-data request derives its organization from a validated active membership, never from a request body or tenant header.
- Every tenant database transaction sets `app.current_organization_id`; missing context exposes no tenant rows and cross-tenant writes fail at PostgreSQL.
- Production refuses to start if tenant RLS is incomplete or the effective application role is a superuser or has `BYPASSRLS`.
- A resource identifier belonging to another organization is treated as not found.
- Membership role changes and deactivation take effect even while an older JWT remains unexpired.
- Every production access token is bound to an active server-side session and one current organization membership.
- Refresh tokens are never stored in browser JavaScript storage or plaintext in PostgreSQL; replay of the previous token revokes the session.
- MFA setup seeds are returned once, encrypted before persistence, and never included in user or session responses.
- An MFA challenge and recovery code can each establish at most one session.
- OIDC does not auto-provision or link accounts unless an operator explicitly enables verified-email linking.
- AWS secret access keys are never returned by an API or delivered to frontend code.
- Account collection uses the selected account's STS AssumeRole session and verifies the resulting AWS account ID before reading resources.
- Every sensitive state-changing API request is audited without its body or token.
- An ingestion response reports success only after the normalized event is committed to PostgreSQL.
- Multiple workers cannot hold the same active event lease, and failed events remain retryable or replayable.
- Detection starts only after the event archive is persisted and its checksum is recorded.
- Hot-database retention deletes only completed events with confirmed archive metadata; dead letters remain available to operators.
- Production traffic terminates TLS before reaching the application.
