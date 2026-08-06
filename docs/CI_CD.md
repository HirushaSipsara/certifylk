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

The workflow trims whitespace from all four GitHub environment variables and validates the normalized values before requesting AWS credentials. The Systems Manager command list is executed by `/bin/sh`, so its wrapper uses portable `set -eu`. It explicitly invokes `infra/production/scripts/deploy.sh` with Bash; the deployment script itself retains Bash strict mode.

## Verified production run

The complete CI-to-production chain passed on 2026-08-06 for commit `77cd9cbbf6bc42533bfa87e9c2ebf0692a0d577d`:

- CI completed successfully for the pushed `main` commit.
- `Deploy production` published both commit-SHA images.
- GitHub obtained short-lived AWS credentials through OIDC.
- Systems Manager deployed the exact commit to EC2.
- Migration, catalogue seed, container health, and public HTTPS checks passed.
- The public landing page, `/api/v1/health`, and `/api/v1/ready` returned healthy responses at <https://certifylk.duckdns.org>.

## GitHub configuration

Create an environment named `production`. Restrict it to `main`, prevent administrator bypass when available, and require a reviewer when the repository plan supports it. Add these environment variables (not secrets):

| Variable | Example | Purpose |
|---|---|---|
| `AWS_REGION` | `ap-south-1` | Region containing EC2 and the deployment IAM role. |
| `AWS_ROLE_ARN` | `arn:aws:iam::622215957056:role/certifylk-github-deploy` | OIDC role assumed by the workflow. |
| `EC2_INSTANCE_ID` | `i-00e924bf43a9d1fbe` | SSM-managed production instance. |
| `PRODUCTION_DOMAIN` | `certifylk.duckdns.org` | Deployment URL shown by GitHub. |

No AWS access key, database password, Gemini key, SSH private key, or GHCR read token belongs in GitHub workflow YAML. The deploy job needs `id-token: write` only to obtain the OIDC token and `contents: read`; its IAM role grants the narrow SSM calls documented in `AWS_EC2_SETUP.md`.

Enter the values without surrounding quotes and avoid trailing spaces. The workflow normalizes whitespace defensively, but the stored values should still be clean.

The production role trusts the immutable GitHub OIDC subject:

```text
repo:HirushaSipsara@127508250/certifylk@1324306736:environment:production
```

Its attached customer-managed policy restricts `ssm:SendCommand` to `AWS-RunShellScript` and instance `i-00e924bf43a9d1fbe`. Invocation status and cancellation are allowed separately because AWS does not support narrowing those calls to a single invocation before its command ID exists.

The built-in `GITHUB_TOKEN` publishes packages. For a private package, the EC2 host separately uses a read-only package token stored in `infra/production/.env.registry`, which is gitignored and mode `600`.

## Failure behavior

- Any CI job failure prevents the deploy workflow condition from passing.
- A build/publish failure prevents the deploy job.
- SSM output and final status are surfaced in the workflow log.
- `deploy.sh` does not record a release until public health checks pass.
- If the new release is unhealthy and a previous release exists, the script restores previous application images. It never destroys volumes or silently downgrades a schema.

Rerun CI after fixing the cause. Do not manually retag or deploy a failed commit.

Common failure signatures:

- `AWS_REGION is invalid or contains whitespace`: remove spaces from the GitHub environment value; the current workflow also normalizes it.
- `Not authorized to perform sts:AssumeRoleWithWebIdentity`: compare the immutable OIDC subject above with the role trust policy and reapply Terraform.
- `not authorized to perform ssm:SendCommand`: reapply Terraform and confirm the exact managed deployment policy is attached to the role.
- `set: Illegal option -o pipefail`: the SSM command wrapper must use POSIX `set -eu`; only the explicitly invoked Bash script may use `pipefail`.

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
