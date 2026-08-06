# CertifyLK Phase 1 implementation progress

**Last updated:** 2026-08-06

**Current status:** Local MVP complete; production deployment live and test-gated

**Public URL:** <https://certifylk.duckdns.org>

**Verified release:** `77cd9cbbf6bc42533bfa87e9c2ebf0692a0d577d`

**Production AI mode:** deterministic mock

CertifyLK remains a readiness-assessment tool for small Sri Lankan food manufacturers preparing for SLS-related certification. It does not issue, guarantee, or replace SLS certification or an official inspection.

## Milestone status

| Milestone | Status | Evidence |
|---|---|---|
| Canonical documentation | Complete | Product, architecture, API, data, AI, scoring, test, local-development, security, release, and production runbooks are maintained under `docs/`. |
| Four-page guest workflow | Complete | Profile, process, evidence, clarification, and result routes persist UUID-based progress and support refresh recovery. |
| Database and catalogue | Complete | Alembic migration and idempotent seed load 21 requirements, 35 approved questions, and 12 curated LKR recommendations. |
| Deterministic domain engine | Complete | Requirement evaluation, readiness, evidence completeness, ranking, costs, gains, and projections run exclusively in typed Python. |
| AI providers | Complete | Deterministic mock mode drives tests and production demo; the integrated Gemini adapter includes bounded requests, structured-output validation, exact evidence binding, safe errors, retry/fallback, and a backend-only connectivity script. |
| AI transparency and evidence review | Complete | Process/evidence responses expose exact-run provider/fallback metadata; review states show accessible polarity icons/text, documented confidence bands, truthful long-running/error states, and confirmed fallback only. |
| Upload safety | Complete | Generated storage keys, MIME/signature/size checks, unavailable states, and persistent filesystem storage abstraction are active. |
| Automated tests | Passing | Backend, frontend, mock-AI browser E2E, Terraform checks, audits, and production image/Compose validation pass in GitHub CI. |
| Terraform infrastructure | Applied | VPC, subnet, routing, security group, encrypted EC2/EBS, Elastic IP, SSM role, GitHub OIDC role, and AWS budget were created in `ap-south-1`. |
| HTTPS production | Live | DuckDNS resolves to the Elastic IP; Nginx serves the frontend and API with a valid Let's Encrypt certificate. |
| GitHub CI/CD | Passing | CI and `Deploy production` succeeded for release `77cd9cb`; deployment used OIDC, SSM, immutable GHCR tags, migration, seed, and public health gates. |
| Persistence and recovery | Implemented | PostgreSQL and uploads use stable named volumes; deployment performs backups and preserves volumes; rollback and restore runbooks are documented. |

## Production baseline

| Item | Verified value |
|---|---|
| AWS account | `622215957056` |
| AWS region | `ap-south-1` |
| EC2 instance | `i-00e924bf43a9d1fbe` |
| Elastic IP | `3.108.242.97` |
| Hostname | `certifylk.duckdns.org` |
| GitHub deploy role | `arn:aws:iam::622215957056:role/certifylk-github-deploy` |
| Repository path on EC2 | `/opt/certifylk/repository` |
| Release source | GitHub `main`, exact tested commit SHA |
| Production provider | `AI_PROVIDER=mock` |

These identifiers are non-secret operational metadata. Passwords, API keys, tokens, `.env.production`, TLS private keys, and Terraform state are intentionally omitted.

## Verified workflow

1. The landing page provides Start Assessment and Load Sample Assessment.
2. Page 1 saves the product profile and obtains two to five approved adaptive questions.
3. Page 2 accepts exactly five process slots, requires at least three steps, extracts approved process stages, and builds an evidence plan.
4. Page 3 accepts safe image/PDF uploads or unavailable states, records structured observations, and selects final approved questions.
5. Page 4 saves clarifications and invokes deterministic evaluation, scoring, costing, ranking, and projection.
6. The result separates readiness from evidence completeness and shows strengths, gaps, unknowns, LKR actions, expected gains, cumulative projections, explanations, and the certification disclaimer.

The production deployment exposes the same workflow as local development. No production-only product behavior was added.

## Validation record

### GitHub and public production

- GitHub CI run for `77cd9cb` completed successfully on 2026-08-06.
- The dependent `Deploy production` workflow completed successfully for the same SHA.
- GHCR images were published with the full tested SHA; no floating application tag is used.
- GitHub authenticated through OIDC; no long-lived AWS key is stored in GitHub.
- AWS Systems Manager checked out the exact SHA and invoked the Bash deployment script.
- Alembic migration and deterministic seed completed successfully.
- PostgreSQL, FastAPI, Next.js, and Nginx reached healthy state.
- `https://certifylk.duckdns.org/` returned HTTP `200` and rendered CertifyLK.
- `https://certifylk.duckdns.org/api/v1/health` returned `{"status":"ok","service":"CertifyLK API"}`.
- `https://certifylk.duckdns.org/api/v1/ready` returned `{"status":"ready","database":"ok"}`.

### Local product checks

- Ruff formatting and linting passed.
- Mypy passed with no source errors.
- Pytest passed all 14 backend tests, including exact-run metadata, confirmed fallback, and test-only concern persistence/evaluation coverage.
- ESLint and TypeScript strict checks passed.
- Vitest passed eight component tests across five files, including provider/fallback labels, all three evidence polarities, confidence bands, and unknown-polarity defense.
- Next.js optimized production build passed.
- Playwright passed both the complete deterministic chilli-paste browser flow and a manual synthetic evidence-analysis flow showing the actual Mock provider, Unclear polarity, question icon, and `45%` Unclear confidence.
- npm audit reported zero vulnerabilities after reviewed dependency updates.
- The deterministic sample produces readiness `32` with separate strengths, gaps, unknowns, catalogue-only costs, and the disclaimer.

### Local Gemini verification

A backend-only Gemini configuration separately completed all five AI operations with structured Pydantic validation and no fallback:

1. `plan_adaptive_questions`
2. `extract_process`
3. `analyze_evidence`
4. `plan_clarifications`
5. `explain_roadmap`

This does not mean Gemini is enabled in production. Production intentionally remains in mock mode until the EC2-only key is configured and the complete public sample is re-verified.

## Deployment issues resolved

- The first EC2 bootstrap clone failed while the repository was private. After the repository became public, the host repository and protected environment were recovered without putting a GitHub credential in Terraform.
- GitHub's immutable OIDC subject format required the numeric owner and repository IDs in the IAM trust policy.
- The deploy role now has an exact customer-managed SSM policy for `AWS-RunShellScript` and the single production instance, plus invocation status/cancel permissions.
- Trailing whitespace in GitHub environment variables caused validation and IAM targeting failures. Workflow inputs are now normalized and validated before authentication and deployment.
- `AWS-RunShellScript` executes its command list with `/bin/sh`; its wrapper now uses portable `set -eu`. The repository deployment script is still invoked explicitly with Bash and retains `set -Eeuo pipefail`.
- The EC2 `.env.production` file was recovered with a host-generated PostgreSQL password, mock AI mode, `600` permissions, and `certifylk` ownership. Its contents were never printed or committed.
- The frontend production build now creates an empty `public/` directory when no static assets are present.
- AI execution metadata now comes directly from the exact successful `ai_runs` record returned by the call boundary; no latest-run query or persistence change was introduced.
- Process and evidence pages now pause for lightweight review, preserve missing-metadata compatibility, and never claim an internal retry is visible.

## Current limitations

- The topology is one EC2 host and is not highly available.
- DuckDNS is a temporary free hostname. A controlled domain can replace it later without changing product behavior.
- PostgreSQL and uploads persist on the EC2 host; verified off-host backup retention and restore rehearsal remain operational follow-ups.
- Production currently uses deterministic mock AI. Enabling Gemini requires an EC2-only key and another public workflow verification.
- A real production photo/PDF Gemini analysis still needs a deliberate manual validation with non-sensitive fixtures.
- Guest UUID possession grants assessment access; authentication and multi-user privacy controls remain outside Phase 1.
- Curated requirements, readiness mappings, recommendations, and LKR cost bands require domain-expert review before public reliance.
- The deployment does not provide laboratory testing, physical inspection, official submission, or certification decisions.

## Next operational checks

1. Complete the public one-click sample and one upload/unavailable path after each release.
2. Run `certbot renew --dry-run` and verify the Nginx reload hook.
3. Export a backup off EC2 and perform a controlled restore rehearsal using `BACKUP_AND_RESTORE.md`.
4. Configure GitHub branch protection and production approval rules if the current repository plan supports them.
5. Add Gemini only to the protected EC2 environment when live AI is required; never add it to GitHub or Terraform.
6. Review AWS spend and budget alerts while the free-trial credits are active.

## Local commands

```powershell
$env:CERTIFYLK_POSTGRES_PORT = "55432"
docker compose -f infra/local/docker-compose.yml up -d

Push-Location backend
python -m alembic upgrade head
Pop-Location
python scripts/seed_demo_data.py
```

Run the backend and frontend in separate terminals:

```powershell
Set-Location backend
python -m uvicorn app.main:app --reload --port 8000
```

```powershell
Set-Location frontend
npm run dev
```

Run deterministic validation:

```powershell
Push-Location backend
python -m ruff format --no-cache --check app tests
python -m ruff check --no-cache app tests
python -m mypy app
python -m pytest
Pop-Location

Push-Location frontend
npm run lint
npm run typecheck
npm test -- --run
npm run build
Pop-Location
```
