# Cloud Security Monitoring Platform

## Overview

An open-source cloud security monitoring platform designed to monitor cloud workloads, detect security threats, and provide a centralized dashboard for security analysts.

## Objectives

- Collect security events
- Monitor cloud workloads
- Detect suspicious behavior
- Generate alerts
- Provide real-time dashboards

## Technology Stack

- Python
- FastAPI
- PostgreSQL
- Redis
- React
- Docker
- Kubernetes

## Project Status

Production-style SaaS platform with secure multi-account AWS onboarding

### Delivery history

| Phase | Capability | Status |
| --- | --- | --- |
| 0 | Project structure and service scaffolding | Complete |
| 1 | AWS collection and CloudTrail normalization | Complete |
| 2 | PostgreSQL persistence and Alembic migrations | Complete |
| 3 | Detection rules, correlation, and incidents | Complete |
| 4 | Alert and incident operations | Complete |
| 5 | Asset discovery, enrichment, and risk | Complete |
| 6 | Notifications and alert delivery controls | Complete |
| 7 | SOC dashboard and analytics frontend | Complete |
| 8 | Production containers and CI | Complete |
| 9 | Metrics, logging, dashboards, and runtime hardening | Complete |
| 10 | Authentication, RBAC, user administration, and audit logs | Complete |
| 11 | Admin AWS account control panel | Complete |
| 12 | Background collection and scheduling | Complete |
| 13 | Structured logging and audit trail | Complete |
| 14 | PostgreSQL-backed automated verification | Complete |
| 15 | Production container and Render deployment | Complete |
| 16 | Architecture, threat model, IAM, and deployment documentation | Complete |

## Architecture and security

- [Architecture and API design](docs/ARCHITECTURE.md)
- [Threat model](docs/THREAT_MODEL.md)
- [Deployment and hardening guide](docs/DEPLOYMENT.md)
- [Least-privilege AWS monitoring role](infrastructure/aws/monitoring-role.yaml)

AWS account onboarding uses cross-account `sts:AssumeRole`. Administrators can
manage accounts at `/admin/aws-accounts`; the backend independently enforces the
admin role for creation, updates, deletion, validation, and direct collection.
The UI and API never return an external ID or AWS secret credential.

## Phase 10 access control

Phase 10 provides expiring JWT sessions, PBKDF2 password hashing, active-user
validation, `admin`, `analyst`, and read-only `viewer` roles, administrator user
management, and audit records for authenticated API mutations.

Configure the local, Git-ignored `.env` before enabling authentication:

```dotenv
AUTH_ENABLED=true
AUTH_BOOTSTRAP_ADMIN_USERNAME=cloud-admin
AUTH_BOOTSTRAP_ADMIN_EMAIL=cloud-admin@example.com
AUTH_BOOTSTRAP_ADMIN_PASSWORD=replace-with-a-long-random-password
```

The bootstrap administrator is created only when the configured username does
not already exist. After changing authentication configuration, run:

```bash
DEBUG=false docker compose up -d --build backend frontend
```

Open the application at <http://localhost:8080>. Administrators can manage
users and inspect recent audit activity from **Access Management**.

## Tests

Run the complete PostgreSQL-backed backend suite on the Compose network:

```bash
docker compose --profile test run --rm backend-tests
```

Run frontend verification with:

```bash
npm --prefix frontend run lint
npm --prefix frontend run build
```

## Deploy to Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https%3A%2F%2Fgithub.com%2FPushpendra23020%2Fcloud-security-monitoring%2Ftree%2Fmain)

The repository includes a `render.yaml` Blueprint that deploys the frontend and
API as one Docker web service backed by managed PostgreSQL. In Render, choose
**New → Blueprint**, connect this repository, and deploy the `main` branch.
Render prompts for `AUTH_BOOTSTRAP_ADMIN_PASSWORD`. Give the deployed service
an execution identity that can assume customer monitoring roles; do not upload
personal, root-account, or long-lived customer access keys.
