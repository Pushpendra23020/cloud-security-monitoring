# Deployment Guide

## Local Docker Compose

1. Copy `.env.example` to `.env` and replace every placeholder with a generated secret.
2. Run `DEBUG=false docker compose up -d --build`.
3. Open `http://localhost:8080`; API health is at `http://localhost:8000/health`.
4. Run tests with `DEBUG=false docker compose --profile test run --rm backend-tests`.

Compose starts `event-worker` after the API is healthy. Scale it with:

```bash
docker compose up -d --scale event-worker=3
```

## Production

Use the combined image in `deployment/render/Dockerfile` for Render, or the separate backend/frontend Dockerfiles behind an HTTPS reverse proxy on ECS, Kubernetes, EC2, or a VPS. Use managed PostgreSQL, encrypted backups, a managed secret store, restricted outbound networking, and centralized logs. Run `alembic upgrade head` exactly once during release.

### Production launch gate

Before exposing a production URL, complete and record each item below:

1. Create a managed PostgreSQL instance with automated backups, point-in-time recovery where available, and perform one documented restore into an isolated database.
2. Create a dedicated S3 archive bucket with versioning, Object Lock in compliance mode, and a customer-managed KMS key. Configure `EVENT_ARCHIVE_PROVIDER=s3`, `EVENT_ARCHIVE_S3_BUCKET`, and `EVENT_ARCHIVE_S3_KMS_KEY_ID` on the worker. The worker now refuses filesystem archives, missing KMS encryption, or missing retention in production.
3. Generate independent values for `SECRET_KEY`, `AUTH_MFA_ENCRYPTION_KEY`, `EVENT_INGEST_API_KEY`, and `GRAFANA_ADMIN_PASSWORD` in a managed secret store. `AUTH_MFA_ENCRYPTION_KEY` must remain stable; do not rotate it without a migration plan for enrolled devices.
4. Configure a non-owner PostgreSQL runtime role using `deployment/postgres/01-runtime-role.sql`, set `DATABASE_RUNTIME_ROLE` on both web and worker services, and keep migration credentials separate. Startup rejects a role that can bypass forced RLS.
5. Set the real HTTPS domain, configure `AUTH_COOKIE_SECURE=true`, DNS, TLS, allowed CORS origins/trusted hosts, an OIDC provider or administrator MFA policy, and an alert delivery endpoint. Verify a test alert reaches the on-call destination.
6. Run CI, including the migration rollback and dependency audit jobs, then perform a smoke test of login, MFA, a collector, ingestion, archive retrieval, and the queue dead-letter alert.

The API emits HSTS in production and applies CSP, anti-framing, MIME-sniffing, referrer, permissions, and no-store API cache headers. Terminate TLS at the public edge; never send an HSTS-enabled deployment over plain HTTP.

Required secrets are `DATABASE_URL`, `SECRET_KEY`, `EVENT_INGEST_API_KEY`, and the bootstrap administrator password. Do not configure AWS root keys. Give the platform execution identity only permission to assume customer monitoring roles.

## Authentication sessions

Set `ACCESS_TOKEN_EXPIRE_MINUTES=10` and choose the server-side session lifetime with `AUTH_SESSION_EXPIRE_DAYS`. `AUTH_MAX_FAILED_LOGINS` and `AUTH_LOCKOUT_MINUTES` control credential lockout. Hosted HTTPS deployments must use `AUTH_COOKIE_SECURE=true`; `AUTH_COOKIE_SAMESITE=strict` is recommended for the same-origin frontend/API architecture. Compose defaults the secure flag to false only so local `http://localhost` development works.

The browser stores no access or refresh credential in `localStorage`. Access tokens remain in memory, while the refresh cookie is HttpOnly and restricted to `/api/v1/auth`. PostgreSQL stores only SHA-256 refresh-token hashes. Do not place the API on a different site from the frontend without first adding an explicit CSRF design and reviewing the SameSite policy.

Set `AUTH_MFA_ENCRYPTION_KEY` to an independent randomly generated secret and keep it stable for the lifetime of enrolled MFA devices. Losing or rotating it without a migration invalidates existing TOTP enrollments. Tune the PostgreSQL-backed rate limiter with `AUTH_RATE_LIMIT_WINDOW_SECONDS`, `AUTH_RATE_LIMIT_BLOCK_SECONDS`, `AUTH_RATE_LIMIT_PRINCIPAL_ATTEMPTS`, and `AUTH_RATE_LIMIT_IP_ATTEMPTS`.

Set `AUTH_TRUSTED_PROXY_CIDRS` only to the private addresses of the reverse proxies you control. Forwarded client addresses are ignored from every other peer. Compose binds the direct API port to loopback and trusts its private container network; the public frontend remains the normal entry point.

To connect an OpenID Connect provider, register `/api/v1/auth/oidc/callback` as the callback and configure:

```text
OIDC_ENABLED=true
OIDC_ISSUER_URL=https://identity.example.com
OIDC_CLIENT_ID=cloud-sentinel
OIDC_CLIENT_SECRET=managed-secret
OIDC_REDIRECT_URI=https://security.example.com/api/v1/auth/oidc/callback
OIDC_ALLOWED_ALGORITHMS=RS256
OIDC_ALLOWED_EMAIL_DOMAINS=example.com
OIDC_ALLOW_EMAIL_LINKING=false
```

Keep email linking disabled for the safest rollout and pre-link the provider issuer/subject to existing users. If verified-email linking is enabled, configure a strict domain allowlist. The identity provider can supply SAML-to-OIDC federation when customers require SAML.

## PostgreSQL tenant enforcement

Alembic migration `e04f00000005` enables and forces RLS on every tenant-owned table. API and worker sessions set the transaction-local `app.current_organization_id` value used by those policies.

For Compose, `deployment/postgres/01-runtime-role.sql` runs automatically on a fresh database. For an existing volume or managed PostgreSQL, run it once as the database owner:

```bash
psql "$MIGRATION_DATABASE_URL" --file deployment/postgres/01-runtime-role.sql
```

Set `DATABASE_RUNTIME_ROLE=cloud_security_runtime` when the migration connection is allowed to assume that role. Use `MIGRATION_DATABASE_URL` for Alembic and `DATABASE_URL` for application traffic when the platform supplies separate database users. Set `RLS_ENFORCEMENT_REQUIRED=true` in production; startup then rejects missing policies and roles that have superuser or `BYPASSRLS` privileges.

## Durable event workers

Run `python -m app.workers.event_ingestion_worker` as an independent process. The worker needs the same runtime database and notification configuration as the API, but it does not need migration credentials or a public port. Render uses the `cloud-security-event-worker` background service in `render.yaml`.

Tune `EVENT_QUEUE_BATCH_SIZE`, `EVENT_QUEUE_POLL_SECONDS`, `EVENT_QUEUE_MAX_ATTEMPTS`, `EVENT_QUEUE_LOCK_TIMEOUT_SECONDS`, and `EVENT_QUEUE_RETRY_BASE_SECONDS` for workload and processing latency. Monitor `/api/v1/events/queue` per workspace and alert whenever `dead_letter` is non-zero or the queued count grows continuously.

Compose archives canonical event envelopes to the `event_archive_data` volume. For production, create a dedicated S3 bucket with versioning and Object Lock enabled, use a retention mode that meets your compliance obligations, then configure:

```text
EVENT_ARCHIVE_PROVIDER=s3
EVENT_ARCHIVE_S3_BUCKET=your-security-archive
EVENT_ARCHIVE_S3_PREFIX=security-events
EVENT_ARCHIVE_S3_KMS_KEY_ID=your-kms-key-id
EVENT_ARCHIVE_RETENTION_DAYS=365
```

The worker uses compliance-mode retention, conditional object creation, SHA-256 checksums and KMS encryption when a key is configured. Its IAM identity needs only `s3:PutObject`, `s3:GetObject`, `s3:GetObjectRetention`, `s3:PutObjectRetention`, `s3:GetObjectVersion`, and the required KMS encrypt permissions for the configured prefix. Do not grant routine `s3:DeleteObject` or Object Lock governance-bypass permissions.

`EVENT_DATABASE_RETENTION_DAYS` controls hot PostgreSQL history. Cleanup only removes completed, archived records; retry and dead-letter records are retained. Prometheus loads `deployment/prometheus/alerts.yml` to alert on dead letters and pending events older than five minutes.

## Readiness classification

- Development-ready: Compose stack, collectors, normalization, detections, persistence, UI, tests.
- Portfolio-ready: architecture, threat model, IAM template, CI, metrics, dashboards, Render blueprint.
- Production-style: RBAC, audit logs, health checks, non-root containers, STS onboarding model.
- External infrastructure required: TLS/DNS, managed database, managed secrets, queue/worker scaling, OIDC provider configuration, backup restoration drills, WAF and alert delivery endpoints.

## Hardening checklist

- Rotate all secrets and keep `.env` untracked.
- Restrict CORS and trusted hosts to the deployed domain.
- Set a strong bootstrap password, then remove bootstrap credentials after provisioning.
- Deploy `infrastructure/aws/monitoring-role.yaml` in each monitored account.
- Enable database encryption, backups, retention, and restore testing.
- Keep migration credentials out of the application runtime and verify forced RLS whenever adding a tenant-owned table.
- Add a managed secret provider for external IDs.
- Require MFA for privileged accounts, connect the production OIDC provider, and add edge-level volumetric protection; application-level distributed authentication limits are implemented.
- Pin and scan images and dependencies; review IAM permissions on every collector change.
