# Production release checklist

## Before merge

- [ ] Product scope, API contracts, readiness scoring, costing, and AI safety behavior are unchanged unless explicitly approved and documented.
- [ ] Every schema change has an Alembic migration and `DATA_MODEL.md` update.
- [ ] New/changed endpoints are reflected in `API_CONTRACT.md`.
- [ ] `make check` passes locally.
- [ ] Dependency audits have no unresolved applicable high/critical findings.
- [ ] Frontend and backend production images build cleanly.
- [ ] Terraform formatting/validation passes and any infrastructure plan has been reviewed before apply.
- [ ] No secret, private key, environment file, upload, backup, or log is staged.
- [ ] GitHub Actions and base image changes are reviewed.
- [ ] Migrations are backward-compatible with the immediately previous application release.

## GitHub and infrastructure readiness

- [ ] `main` protection requires all CI jobs.
- [ ] The `production` environment is restricted to `main` and has the intended approval rule.
- [ ] AWS OIDC trust matches the exact repository/environment subject.
- [ ] The trust subject uses the immutable GitHub owner/repository IDs, not only mutable names.
- [ ] The deploy role has the exact managed SSM policy for `AWS-RunShellScript` and the intended EC2 instance.
- [ ] The EC2 instance is online in Systems Manager.
- [ ] DNS resolves to the production Elastic IP.
- [ ] Certificate is valid and `certbot renew --dry-run` passes.
- [ ] EC2 disk, memory, and backup capacity are sufficient.
- [ ] `.env.production` has no example placeholders and is mode `600`.
- [ ] Gemini mode has a valid backend-only key, or deterministic mock mode is an intentional release decision.
- [ ] GHCR packages are public or the EC2 read-only registry token works.
- [ ] `AWS_REGION`, `AWS_ROLE_ARN`, `EC2_INSTANCE_ID`, and `PRODUCTION_DOMAIN` contain no surrounding or trailing whitespace.

## Deployment

- [ ] Merge/push the reviewed commit to `main`.
- [ ] Confirm all CI jobs pass for that exact SHA.
- [ ] Confirm frontend/backend GHCR images use that full SHA and no floating application tag.
- [ ] Approve the protected GitHub production deployment when prompted.
- [ ] Confirm the SSM deployment command succeeds.
- [ ] Confirm the SSM `/bin/sh` wrapper uses portable `set -eu` and invokes `deploy.sh` explicitly with Bash.
- [ ] Confirm a pre-deployment backup directory contains `COMPLETE` and valid SHA256 hashes.
- [ ] Confirm Alembic and deterministic catalogue synchronization completed.
- [ ] Confirm the recorded production current release equals the tested SHA.

## Public verification

- [ ] `https://<domain>/` loads without mixed content or browser certificate warnings.
- [ ] `/api/v1/health` and `/api/v1/ready` return `200` with request IDs where applicable.
- [ ] Start Assessment creates and resumes a guest UUID assessment.
- [ ] Load Sample Assessment reaches a result with score, confidence/completeness, strength, gap, LKR cost, projected gain, and disclaimer.
- [ ] At a minimum, test one supported evidence upload/unavailable path within configured size limits.
- [ ] Confirm browser developer tools reveal no Gemini key, database credential, internal hostname, or insecure request.
- [ ] Review Nginx, backend, frontend, and PostgreSQL logs for errors and accidental sensitive content.

## Failure and rollback

- [ ] Stop and diagnose if any gate or public verification fails; do not mark the release successful manually.
- [ ] Use `bash infra/production/scripts/rollback.sh` for application-image rollback to the recorded previous SHA.
- [ ] Do not run an Alembic downgrade automatically.
- [ ] Follow `BACKUP_AND_RESTORE.md` only when a data/schema restore is explicitly approved.
- [ ] Record the failed SHA, symptoms, rollback/restore choice, and final health status.

## Verified baseline release

The following baseline was completed on 2026-08-06 and is not a substitute for repeating the checklist on future releases:

- Commit: `77cd9cbbf6bc42533bfa87e9c2ebf0692a0d577d`
- CI: successful
- GitHub `Deploy production`: successful
- URL: <https://certifylk.duckdns.org>
- Landing page: HTTP `200`
- API health: `ok`
- Database readiness: `ready`
- Deployment path: GitHub OIDC to AWS Systems Manager
- AI mode: deterministic mock
