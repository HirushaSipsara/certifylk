# CertifyLK

CertifyLK is a certificate-specific guidance and readiness platform for small Sri Lankan food manufacturers. It combines a database-backed certification knowledge base, bounded AI reasoning and evidence extraction, and deterministic scoring/costing to explain which pathway applies and what the manufacturer should improve next.

> CertifyLK does not issue, guarantee, or replace certification, regulatory approval, laboratory testing, or an official inspection. Catalogue entries marked unverified must be confirmed with the named authority or standards body.

## Authorized tracks

- **Product Quality:** the active pilot is Fresh Fruit Cordial with SLS Mark and relevant food-registration guidance.
- **Process & System:** SLS GMP, SLS HACCP, and ISO 22000:2018 readiness for Sri Lankan food manufacturers.

The repository is in a **transitional redesign**. The database-backed catalogue, Track 1 wizard, Track 2 entry flow, applicability reasoning, Assessment Hub, legacy assessment workflow, AI adapters, deployment, and tests exist. The scheme-specific evidence, evaluation, scoring, roadmap, verified source content, PDF export, education page, and dashboard are not yet complete. See [Implementation progress](docs/IMPLEMENTATION_PROGRESS.md) and the [Full implementation plan](docs/FULL_IMPLEMENTATION_PLAN.md).

## Quick start

Prerequisites: Python 3.10+, Node.js 20+, Docker Compose, and optionally GNU Make.

```bash
copy backend\.env.example backend\.env
copy frontend\.env.example frontend\.env.local
make db-up
make install
make migrate
make seed
make backend-dev
# in another terminal
make frontend-dev
```

Open <http://localhost:3000>. API docs are at <http://localhost:8000/docs>.

Use `make test` for automated tests and `make check` for format, lint, type, test, and build gates. Direct PowerShell and Bash commands are in [Local development](docs/LOCAL_DEVELOPMENT.md).

## Repository map

- `docs/`: canonical product, domain, API, AI, test, delivery, and completion plans.
- `frontend/`: Next.js App Router UI for both tracks and the assessment experience.
- `backend/`: FastAPI, SQLAlchemy/Alembic, certificate catalogue, domain engines, and Mock/Gemini adapters.
- `infra/local/`: local PostgreSQL.
- `infra/production/`: single-host Compose, Nginx, backup, health, deploy, and rollback scripts.
- `infra/terraform/`: AWS EC2/network/IAM/OIDC/SSM provisioning.
- `.github/workflows/`: test-gated CI and immutable production deployment.
- `sample-data/`: legacy deterministic chilli-paste regression fixture.

## Production

The existing single-host deployment is documented at [Production deployment](docs/PRODUCTION_DEPLOYMENT.md). Infrastructure is reusable for the redesign, but a previously verified release is not proof that the current working tree or all new Track 2 paths are deployed. Release only a commit whose complete CI suite and updated public smoke checklist pass.

Never commit backend/frontend environment files, Gemini credentials, database passwords, AWS credentials, registry tokens, uploaded evidence, backups, Terraform state, or TLS private keys.
