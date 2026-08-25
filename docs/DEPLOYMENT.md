# Deployment Guide

## Local Docker Compose

1. Copy `.env.example` to `.env` and replace every placeholder with a generated secret.
2. Run `DEBUG=false docker compose up -d --build`.
3. Open `http://localhost:8080`; API health is at `http://localhost:8000/health`.
4. Run tests with `DEBUG=false docker compose --profile test run --rm backend-tests`.

## Production

Use the combined image in `deployment/render/Dockerfile` for Render, or the separate backend/frontend Dockerfiles behind an HTTPS reverse proxy on ECS, Kubernetes, EC2, or a VPS. Use managed PostgreSQL, encrypted backups, a managed secret store, restricted outbound networking, and centralized logs. Run `alembic upgrade head` exactly once during release.

Required secrets are `DATABASE_URL`, `SECRET_KEY`, `EVENT_INGEST_API_KEY`, and the bootstrap administrator password. Do not configure AWS root keys. Give the platform execution identity only permission to assume customer monitoring roles.

## Readiness classification

- Development-ready: Compose stack, collectors, normalization, detections, persistence, UI, tests.
- Portfolio-ready: architecture, threat model, IAM template, CI, metrics, dashboards, Render blueprint.
- Production-style: RBAC, audit logs, health checks, non-root containers, STS onboarding model.
- External infrastructure required: TLS/DNS, managed database, managed secrets, queue/worker scaling, MFA/SSO, backup restoration drills, WAF and alert delivery endpoints.

## Hardening checklist

- Rotate all secrets and keep `.env` untracked.
- Restrict CORS and trusted hosts to the deployed domain.
- Set a strong bootstrap password, then remove bootstrap credentials after provisioning.
- Deploy `infrastructure/aws/monitoring-role.yaml` in each monitored account.
- Enable database encryption, backups, retention, and restore testing.
- Add a managed secret provider for external IDs.
- Enable MFA/SSO, rate limiting, and HttpOnly cookie sessions before internet-wide production use.
- Pin and scan images and dependencies; review IAM permissions on every collector change.
