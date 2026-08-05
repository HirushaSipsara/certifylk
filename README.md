# CertifyLK

CertifyLK is a local-first Phase 1 MVP that helps small Sri Lankan food manufacturers assess preparation readiness for SLS-related food certification. It provides a four-page guided assessment, deterministic scoring and costing, evidence-aware recommendations, mock AI for reproducible demos, and an optional Gemini adapter.

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
- `scripts/`: seed, reset, and local health-check helpers.
- `sample-data/`: deterministic chilli-paste demo inputs.

Production deployment, AWS, EC2, Nginx, CI/CD, and GitHub Actions are deliberately outside Phase 1.
