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
- `.github/workflows/`: test-gated CI and commit-SHA production deployment through AWS Systems Manager.
- `scripts/`: seed, reset, and local health-check helpers.
- `sample-data/`: deterministic chilli-paste demo inputs.

## Production delivery

Production delivery is a separate infrastructure stage; it does not change Phase 1 product scope. The lowest-manual-work path is [Terraform automation](infra/terraform/README.md). To understand or finish the credentials connection manually, use [AWS credentials and final deployment](docs/AWS_CREDENTIALS_AND_FINAL_DEPLOYMENT.md). The full operator reference is [AWS and GitHub deployment guide](docs/AWS_GITHUB_DEPLOYMENT_GUIDE.md). The repository contains the deployment workflow, but an actual public URL still requires access to the operator's AWS account, GitHub repository, domain/DNS, TLS email, and backend-only production secrets.
