# CertifyLK

CertifyLK is a Phase 1 MVP that helps small Sri Lankan food manufacturers assess preparation readiness for SLS-related food certification. It provides a four-page guided assessment, deterministic scoring and costing, evidence-aware recommendations, mock AI for reproducible demos, an optional Gemini adapter, and a production delivery path that preserves the same workflow.

> CertifyLK is a readiness-assessment tool. It does not issue, guarantee, or replace SLS certification or an official inspection.

## Quick start

Prerequisites: Python 3.10+, Node.js 20+, Docker with Compose, and GNU Make (optional on Windows).

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

Open <http://localhost:3000>. API documentation is at <http://localhost:8000/docs>.

Use `make test` for all automated tests and `make check` for formatting, linting, types, and tests. See [Local development](docs/LOCAL_DEVELOPMENT.md) for direct PowerShell/Linux commands and troubleshooting.

## Repository map

- `docs/`: canonical product, architecture, API, data, AI, scoring, and test documentation.
- [`docs/IMPLEMENTATION_PROGRESS.md`](docs/IMPLEMENTATION_PROGRESS.md): current milestone, verification, live Gemini, limitations, and next-step status.
- `frontend/`: Next.js App Router application.
- `backend/`: FastAPI application, Alembic migration, and pytest suite.
- `infra/local/`: local PostgreSQL Compose service only.
- `infra/production/`: HTTPS Nginx, private application/data services, persistent volumes, and release operations for one EC2 host.
- `infra/terraform/`: repeatable AWS, EC2, IAM/OIDC, SSM, networking, Elastic IP, and budget provisioning.
- `.github/workflows/`: test-gated CI and commit-SHA production deployment through AWS Systems Manager.
- `scripts/`: seed, reset, and local health-check helpers.
- `sample-data/`: deterministic chilli-paste demo inputs.

## Production delivery

Production delivery is a separate infrastructure stage; it does not change Phase 1 product scope. The verified Phase 1 deployment is available at <https://certifylk.duckdns.org> and currently uses deterministic mock AI. Pushes to `main` are test-gated, published as full-commit-SHA GHCR images, and deployed to EC2 through GitHub OIDC and AWS Systems Manager.

Use [Terraform automation](infra/terraform/README.md) for infrastructure, [Production deployment](docs/PRODUCTION_DEPLOYMENT.md) for routine operations, and [AWS credentials and final deployment](docs/AWS_CREDENTIALS_AND_FINAL_DEPLOYMENT.md) for credential boundaries and first-time recovery. Never commit the EC2 production environment, PostgreSQL password, Gemini key, registry token, Terraform state, or AWS access keys.
