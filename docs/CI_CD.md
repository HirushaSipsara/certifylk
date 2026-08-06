# CI/CD

## Continuous integration

`.github/workflows/ci.yml` runs for pull requests to `main`, pushes to `main`, and manual checks. Permissions default to read-only. Concurrent runs for the same ref cancel older work.

The required jobs are:

- Backend: Ruff format/lint, strict mypy, pytest, `pip-audit`, and Bandit.
- Frontend: `npm ci`, high-severity dependency audit, ESLint, TypeScript, Vitest, and a production Next.js build using `/api/v1`.
- Mock-AI E2E: PostgreSQL service, Alembic migration, deterministic seed, real FastAPI/Next.js processes, and Playwright’s chilli-paste happy path.
- Terraform: locked-provider initialization without a backend, recursive formatting check, and static configuration validation without AWS credentials.
- Containers: clean builds of both production Dockerfiles and validation of production Compose interpolation.

Third-party actions are pinned to full commit SHAs. Dependabot or a reviewed maintenance change should update those pins; never replace them with a moving branch.

Protect `main` and require the `Backend checks`, `Frontend checks`, `Mock-AI happy path`, `Terraform checks`, and `Production container builds` checks. Direct pushes that bypass these checks should be disabled.

## Continuous deployment

`.github/workflows/deploy.yml` listens only for a completed `CI` workflow. It proceeds only when the triggering run:

- concluded successfully;
- was caused by a push;
- tested the `main` branch.

The publish job creates GHCR images tagged with the exact tested 40-character commit SHA. The deploy job uses the GitHub `production` environment, authenticates to AWS through OIDC, and sends the exact SHA to the EC2 instance through Systems Manager. A concurrency group permits only one production deployment at a time.

## GitHub configuration

Create an environment named `production`. Restrict it to `main`, prevent administrator bypass when available, and require a reviewer when the repository plan supports it. Add these environment variables (not secrets):

| Variable | Example | Purpose |
|---|---|---|
| `AWS_REGION` | `ap-south-1` | Region containing EC2 and the deployment IAM role. |
| `AWS_ROLE_ARN` | `arn:aws:iam::123456789012:role/certifylk-github-deploy` | OIDC role assumed by the workflow. |
| `EC2_INSTANCE_ID` | `i-0123456789abcdef0` | SSM-managed production instance. |
| `PRODUCTION_DOMAIN` | `certifylk.example.com` | Deployment URL shown by GitHub. |

No AWS access key, database password, Gemini key, SSH private key, or GHCR read token belongs in GitHub workflow YAML. The deploy job needs `id-token: write` only to obtain the OIDC token and `contents: read`; its IAM role grants the narrow SSM calls documented in `AWS_EC2_SETUP.md`.

The built-in `GITHUB_TOKEN` publishes packages. For a private package, the EC2 host separately uses a read-only package token stored in `infra/production/.env.registry`, which is gitignored and mode `600`.

## Failure behavior

- Any CI job failure prevents the deploy workflow condition from passing.
- A build/publish failure prevents the deploy job.
- SSM output and final status are surfaced in the workflow log.
- `deploy.sh` does not record a release until public health checks pass.
- If the new release is unhealthy and a previous release exists, the script restores previous application images. It never destroys volumes or silently downgrades a schema.

Rerun CI after fixing the cause. Do not manually retag or deploy a failed commit.

## Local equivalents

```bash
make check
(cd frontend && npm audit --audit-level=high)
python -m pip_audit --local --skip-editable
docker build -t certifylk-backend:local backend
docker build --build-arg NEXT_PUBLIC_API_BASE_URL=/api/v1 -t certifylk-frontend:local frontend
docker compose --env-file infra/production/.env.production.example -f infra/production/docker-compose.yml --profile operations config --quiet
```

The local development Compose file and Make targets are unchanged.
