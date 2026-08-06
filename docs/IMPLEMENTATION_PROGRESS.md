# CertifyLK Phase 1 implementation progress

**Last updated:** 2026-08-06  
**Current status:** Local Phase 1 MVP complete; production delivery implemented locally and awaiting external AWS/DNS/GitHub provisioning
**Scope:** Sri Lankan food-manufacturing readiness for SLS-related certification preparation only

CertifyLK remains a readiness-assessment tool. It does not issue, guarantee, or replace SLS certification or an official inspection.

## Progress summary

| Milestone | Status | Current evidence |
|---|---|---|
| Canonical product and technical documentation | Complete | All required documents exist under `docs/`; `AGENTS.md` defines scope and engineering rules. |
| Monorepo and local infrastructure | Complete | Next.js frontend, FastAPI backend, PostgreSQL 16 Compose service, scripts, sample data, and Make targets exist. |
| Database model and catalogue | Complete | Initial Alembic migration applied; 21 requirements, 35 approved questions, and 12 LKR recommendations seeded. |
| Four-page guest assessment | Complete | Profile, process, evidence, clarification, and result routes work with UUID-based resume state. |
| Deterministic readiness engine | Complete | Requirement evaluation, category normalization, readiness, evidence completeness, costs, gains, projections, and ranking are deterministic Python. |
| Mock AI | Complete | Deterministic provider drives automated tests and the reproducible chilli-paste demo without a key. |
| Gemini AI | Complete and live-verified | `gemini-3.6-flash` completed all five AI operations with structured validation and no fallback in the final live workflow. |
| Local file evidence | Complete | Safe generated storage keys, MIME/signature/size validation, unavailable states, and local storage abstraction are implemented. |
| Frontend experience | Complete | Mobile-first pages, accessibility labels, loading/error states, refresh recovery, sample loading, and reusable result components are implemented. |
| Automated validation | Passing | Backend, frontend, API integration, browser E2E, optimized build, and dependency audit passed. |
| Production containers and proxy | Implemented and locally validated | Non-root application images, digest-pinned base/service images, private-network Compose, Nginx HTTPS, persistent PostgreSQL/uploads, and health checks passed an isolated production-stack smoke test. |
| Release operations | Implemented and locally validated | Explicit migrations/seeding, backup creation and hash verification, persistence across restart, HTTPS health gating, application rollback, and certificate reload scripts are implemented. A real prior-release rollback remains a release-environment check. |
| GitHub CI/CD | Implemented; not yet run on GitHub | Full-SHA-pinned CI actions, immutable GHCR tags, GitHub OIDC, and SSM deployment workflow are committed as configuration. |
| Public AWS/HTTPS deployment | Blocked on operator prerequisites | No AWS credentials/profile, EC2 instance ID, GitHub production environment, pushed remote commit, domain, or DNS target was available in this workspace. |
| Unified AWS/GitHub operator guide | Complete | `AWS_GITHUB_DEPLOYMENT_GUIDE.md` provides the ordered Free Plan safeguards, EC2, IAM, SSM, GitHub OIDC, GHCR, DNS, Certbot, deployment, verification, backup, rollback, troubleshooting, and teardown procedure. |
| AWS credentials and final deployment guide | Complete | `AWS_CREDENTIALS_AND_FINAL_DEPLOYMENT.md` focuses on OIDC trust, least-privilege IAM, exact GitHub environment variables, EC2-only secrets, GHCR access, and the steps from first push through a verified public deployment. |
| Terraform production automation | Implemented; live apply pending | `infra/terraform` provisions the AWS network, EC2/EIP, SSM access, GitHub OIDC role, optional Route 53/budget/GitHub variables, and secret-free host bootstrap. A live apply requires the operator's authenticated AWS account, real domain, and optional GitHub token. |

## Completed user workflow

1. `/` presents the mission, disclaimer, estimated duration, Start Assessment, and Load Sample Assessment actions.
2. `/assessment/[assessmentId]/profile` saves the business/product profile and requests two to five approved adaptive questions.
3. `/assessment/[assessmentId]/process` accepts exactly five slots with at least three completed steps, saves adaptive answers, extracts structured stages, and creates the evidence plan.
4. `/assessment/[assessmentId]/evidence` supports requested image/PDF uploads or unavailable states, validates files, analyzes supplied evidence, and plans final questions.
5. `/assessment/[assessmentId]/clarification` accepts three to five approved clarifications and advances the assessment to scoring.
6. `/assessment/[assessmentId]/result` displays readiness, separate evidence completeness, category scores, strengths, gaps, unknowns, prioritized LKR actions, expected gains, cumulative projections, explanations, and the disclaimer.

The assessment UUID is retained in the URL and browser local storage. Saved API state supports refresh recovery without authentication.

## Backend progress

- All required `/api/v1` system, assessment, page-workflow, evidence, completion, and result endpoints are implemented.
- Pydantic request/response schemas, consistent error envelopes, request IDs, transition validation, and documented `409`, `413`, `415`, and `422` behavior are active.
- SQLAlchemy models and the first Alembic migration cover all 15 required entities.
- PostgreSQL catalogue seeding is idempotent.
- Uploaded files use generated storage keys under the configured local upload directory; raw names are metadata only.
- The future `S3StorageProvider` boundary exists but contains no AWS calls.
- Logs and `ai_runs` omit prompts, raw document content, and credentials.

## AI progress

### Mock mode

- Remains the default in `backend/.env.example`.
- Requires no API key.
- Produces repeatable approved questions, process stages, evidence observations, clarification plans, and roadmap explanations.
- Is forced during automated tests even when the developer's local `.env` enables Gemini, preventing accidental network calls and API charges.

### Live Gemini mode

- Active local configuration: `AI_PROVIDER=gemini` and `GEMINI_MODEL=gemini-3.6-flash`.
- The API key is stored only in ignored `backend/.env`; the commit-ready `.env.example` contains a blank key.
- The key is sent with the `x-goog-api-key` request header rather than a URL query parameter.
- Deprecated sampling parameters were removed for Gemini 3.6 compatibility.
- Structured responses are validated through Pydantic before use.
- Adaptive and clarification question IDs are checked against backend-supplied candidates.
- Approved process tags are supplied in the payload and encoded as an enum in the structured-output schema.
- Evidence request IDs and requirement IDs are whitelisted before observations are persisted.
- Gemini is retried once; deterministic mock fallback runs only when enabled and both outcomes are recorded.

The final live chilli-paste assessment recorded these successful Gemini operations, all using `gemini-3.6-flash` with `fallback_used=false`:

1. `plan_adaptive_questions`
2. `extract_process`
3. `analyze_evidence`
4. `plan_clarifications`
5. `explain_roadmap`

## Verification evidence

### Backend

- Ruff format check: 51 files formatted correctly.
- Ruff lint: passed.
- Mypy: no issues in 46 source files.
- Pytest: 12 passed.
- One non-product Starlette/FastAPI test-client deprecation warning remains.

### Frontend

- TypeScript strict check: passed.
- ESLint: passed.
- Vitest: 5 component tests passed across 4 files.
- Next.js optimized build: passed.
- Playwright: one complete browser happy path passed.
- npm audit: zero vulnerabilities after dependency upgrades and safe transitive overrides.

### Production delivery

- Backend and frontend production images built successfully from the repository Dockerfiles.
- The complete isolated Compose stack reached healthy state with PostgreSQL, upload initialization, Alembic migration, deterministic catalogue seed, FastAPI, Next.js, and Nginx.
- Only Nginx published host ports; PostgreSQL, FastAPI, and Next.js remained private Compose services.
- A locally trusted smoke certificate verified the HTTPS health script, landing page, API health, and database readiness routes.
- The sample endpoint and result endpoint completed through Nginx with readiness 32, two strengths, ten gaps, eleven LKR roadmap actions, and the certification disclaimer.
- A full stack stop/start retained and returned the same assessment result from the persistent PostgreSQL volume.
- The backup script produced a PostgreSQL custom-format dump, upload archive, release metadata, completion marker, and passing SHA256 manifest; `pg_restore --list` validated the dump structure.
- Production Compose interpolation, Bash syntax, GitHub workflow YAML parsing, and actionlint 1.7.12 passed locally.
- An isolated Python dependency audit reported no known vulnerabilities; Bandit reported no medium-or-higher findings; npm audit reported zero vulnerabilities; the secret scan found no unexpected credential candidates.

### Local development services

The normal local-development stack was previously verified independently of the isolated production smoke stack:

- Frontend: `http://localhost:3000` returned HTTP 200.
- API: `http://localhost:8000/api/v1/health` returned `ok`.
- Database readiness: `http://localhost:8000/api/v1/ready` returned `ready`.
- API documentation: `http://localhost:8000/docs`.
- PostgreSQL uses host port `55432` on this workstation because another local PostgreSQL service already occupies `5432`.

## Demo results

### Deterministic mock sample

The documented chilli-paste fixture produces a reproducible readiness score of 32 in mock mode, with separate strengths, gaps, unknowns, and catalogue-derived LKR actions.

### Live Gemini sample

- Assessment ID: `51916359-b2a2-4b8f-94dd-9de867393450`
- Result route: `http://localhost:3000/assessment/51916359-b2a2-4b8f-94dd-9de867393450/result`
- Status: completed
- Readiness: 20
- Evidence completeness: 33%
- Confirmed strengths: 1
- Possible gaps: 8
- Unknown requirements: 12
- Roadmap actions: 12
- Currency: LKR

The live and mock scores differ because Gemini may choose different approved adaptive/clarification questions and approved process tags. Once those structured inputs are persisted, scoring, costs, priorities, and projections remain deterministic.

## Issues resolved during implementation

- Avoided a conflict with the workstation's existing PostgreSQL instance by running the CertifyLK Compose database on host port `55432`.
- Upgraded the frontend test toolchain and transitive PostCSS/Sharp packages, reducing the npm audit result to zero vulnerabilities.
- Configured Vitest's current structured JSX transformation and native config loader for the managed Windows filesystem.
- Disabled pytest's cache provider because the managed filesystem rejected `.pytest_cache` writes.
- Moved a mistakenly populated Gemini key out of `.env.example` into ignored `backend/.env` and restored the example safely.
- Replaced Gemini query-string authentication with a request header to prevent credentials appearing in request URLs or error logs.
- Removed deprecated Gemini 3.6 sampling parameters.
- Added the process-tag whitelist to the prompt payload and generated JSON schema after live validation initially rejected invented tags.
- Forced mock mode in tests so a live developer configuration cannot make network calls.

## Current limitations and boundaries

- The final live workflow analyzed an evidence plan whose sample slots were marked unavailable. Real Gemini multimodal analysis of a user-uploaded photo and PDF still needs a manual live validation fixture.
- Gemini output can vary while remaining inside the approved schemas and whitelists; the deterministic mock remains the reproducible judging/development path.
- Gemini usage can incur quota or billing charges depending on the Google AI project.
- If the current key was previously committed, uploaded, or shared while inside `.env.example`, it should be rotated in Google AI Studio.
- Guest UUID possession grants local assessment access; authentication/privacy design is deferred.
- Cost bands and readiness mappings are curated demo interpretations and require domain review before public reliance.
- The tool does not perform laboratory testing, physical inspection, official application submission, or certification decisions.
- GNU Make and WSL were unavailable in the managed Windows validation environment; documented direct PowerShell commands were used instead.
- GitHub-hosted CI, GHCR publishing, AWS OIDC, SSM deployment, Certbot issuance/renewal, and rollback between two real published releases cannot be executed until their external accounts, domain, instance, and repository environment are provisioned.

Production delivery is now implemented as a separate infrastructure stage without altering product behavior. It has not yet been deployed publicly: this workstation has no configured AWS credentials, EC2 target, GitHub production environment, or production domain/DNS. The single-EC2 topology is not highly available, and application-managed cloud storage remains unimplemented; uploads persist on the encrypted EC2 volume and are included in documented backups.

## Recommended next checks

1. Upload one small supported production photo and one PDF through the normal evidence page with Gemini enabled, then confirm the recorded observations use only allowed request and requirement IDs.
2. Manually inspect Gemini explanations for plain language and non-certifying wording across several products within the locked food-manufacturing scope.
3. Rotate the Gemini key if it may have left the workstation, then update only `backend/.env`.
4. Obtain domain-expert review of seeded requirements, evaluation mappings, recommendations, and LKR cost review dates.
5. Preserve mock mode for repeatable tests and demonstrations; enable Gemini only for explicit live evaluation.
6. Provision the documented AWS/GitHub/DNS prerequisites, push the tested commit, run the GitHub workflows, and record the resulting public HTTPS URL and external smoke results here.

## Current local commands

Start the existing port-adjusted database from the repository root:

```powershell
$env:CERTIFYLK_POSTGRES_PORT = "55432"
docker compose -f infra/local/docker-compose.yml up -d
```

Run migrations and seed:

```powershell
Push-Location backend
python -m alembic upgrade head
Pop-Location
python scripts/seed_demo_data.py
```

Start the Gemini-enabled backend and frontend in separate terminals:

```powershell
Set-Location backend
python -m uvicorn app.main:app --reload --port 8000
```

```powershell
Set-Location frontend
npm run dev
```

Run deterministic checks:

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
