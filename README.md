# Cloud Security Monitoring Platform

[![CI](https://github.com/Pushpendra23020/cloud-security-monitoring/actions/workflows/ci.yml/badge.svg)](https://github.com/Pushpendra23020/cloud-security-monitoring/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

An open-source, production-style AWS security monitoring MVP. It connects to
AWS accounts through short-lived STS role sessions, discovers cloud assets,
processes CloudTrail-style security events, evaluates detections and presents
findings, alerts and incidents in a multi-tenant analyst dashboard.

> This repository is suitable for local evaluation and controlled pilot
> deployments. A public production launch still requires managed infrastructure,
> organization-specific security configuration and the launch checks documented
> in [the deployment guide](docs/DEPLOYMENT.md).

![Cloud Sentinel secure sign-in preview](docs/images/login.jpg)

## Capabilities

- Secure cross-account AWS onboarding with `sts:AssumeRole`; no customer
  long-lived access keys are stored.
- AWS asset discovery, security metadata enrichment and risk scoring.
- CloudTrail normalization and PostgreSQL-backed durable event processing.
- Detection findings, alert operations and incident workflows.
- Multi-organization isolation enforced with PostgreSQL row-level security.
- Administrator, analyst and viewer roles with auditable administrative actions.
- Revocable sessions, HttpOnly refresh cookies, TOTP MFA, recovery codes,
  distributed login limits and optional OpenID Connect integration.
- Tamper-resistant event archive support using S3 Object Lock, checksums and KMS.
- Prometheus metrics, Grafana dashboards, structured logs and queue alerts.
- Docker Compose development environment, Render deployment blueprint and CI.

## Architecture

```text
AWS accounts
    │ cross-account IAM role / STS
    ▼
Collectors and event ingestion
    ▼
Durable PostgreSQL queue
    ▼
Normalization, detections and risk scoring
    ▼
Assets ─ Findings ─ Alerts ─ Incidents
    ▼
React dashboard, webhooks, Prometheus and Grafana
```

See the detailed [architecture](docs/ARCHITECTURE.md),
[threat model](docs/THREAT_MODEL.md),
[deployment guide](docs/DEPLOYMENT.md) and
[least-privilege AWS role](infrastructure/aws/monitoring-role.yaml).

## Technology

- Python 3.13, FastAPI, SQLAlchemy and Alembic
- PostgreSQL 17 with forced row-level security
- React 19, Vite and Nginx
- Docker Compose
- Prometheus and Grafana
- AWS STS, CloudTrail, S3 Object Lock and KMS integrations

## Quick start

Requirements: Docker with Compose v2.

```bash
cp .env.example .env
# Replace every placeholder in .env with a generated local value.
docker compose up --build -d
docker compose ps
```

Open the application at <http://localhost:8080>. The API is available only on
the loopback interface at <http://localhost:8000>, Prometheus at
<http://localhost:9090> and Grafana at <http://localhost:3000>.

Never put AWS root credentials or customer access keys in `.env`. Customer
accounts should be connected through the supplied cross-account role template.

## Verification

Run the PostgreSQL-backed backend suite:

```bash
docker compose --profile test run --rm backend-tests
```

Run frontend verification:

```bash
npm --prefix frontend ci
npm --prefix frontend run lint
npm --prefix frontend run build
```

CI also performs migration rollback verification, dependency vulnerability
audits and production container builds.

## Deployment status

The repository includes a Render Blueprint and hardened production containers,
but deploying the blueprint alone does not make the service production-ready.
Before exposing it publicly, configure HTTPS/DNS, managed PostgreSQL backups and
a restore drill, a non-owner database runtime role, managed secrets, an S3
Object Lock archive with KMS, a real alert destination, administrator MFA or
OIDC, monitoring and the smoke tests in the deployment guide.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https%3A%2F%2Fgithub.com%2FPushpendra23020%2Fcloud-security-monitoring%2Ftree%2Fmain)

## Scope and limitations

This is an actively developed MVP, not a replacement for a mature commercial
CNAPP or SIEM. AWS service and detection coverage is currently limited; Azure,
Google Cloud, Kubernetes/container vulnerability scanning, billing and complete
customer lifecycle automation are outside the current implementation.

## Security

Do not report vulnerabilities in public issues. Follow
[SECURITY.md](SECURITY.md) for private disclosure guidance. Never include real
credentials, tenant data or account identifiers in reports.

## License

Licensed under the [Apache License 2.0](LICENSE).
