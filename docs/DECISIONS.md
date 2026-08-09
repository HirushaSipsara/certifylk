# Architecture decision log

## D001 — Guided workflow, not chat

Phase 1 uses four fixed assessment pages. This keeps evidence collection predictable, supports validation, and matches the locked buildathon workflow.

## D002 — Deterministic domain decisions

Requirements, statuses, readiness, completeness, priorities, gains, projections, and costs are calculated in Python using versioned seed data. AI is restricted to extraction, selection, and explanation.

## D003 — Guest UUID state

There is no authentication. The assessment UUID is persisted in the URL/local storage and is the local resume token. This is suitable for the local MVP only.

## D004 — PostgreSQL and JSONB

Normalized entities retain auditable workflow data; JSONB holds bounded, versioned payloads such as option arrays, applicability tags, evaluation evidence references, and result snapshots.

## D005 — Local storage abstraction

Uploads use generated keys beneath a configured local root. An S3-shaped class exists only to preserve the interface boundary; AWS calls are excluded.

## D006 — Mock-first provider

Mock AI is the default for reproducible local development and tests. Gemini is opt-in with backend-only credentials, one retry, structured validation, and configurable fallback.

## D007 — Complete sample endpoint

The sample endpoint creates a new, completed chilli-paste assessment by exercising the same persistence, evaluation, scoring, and roadmap services used by manual completion. It avoids external network calls for a reliable demo.

## D008 — Production/DevOps deferred during local MVP construction

CI/CD, GitHub Actions, AWS, EC2, Nginx, and production Docker deployment were explicitly deferred until the local product was accepted. This historical constraint protected the local vertical slice and is superseded for infrastructure work by D009; the product exclusions remain unchanged.

## D009 — Single-host, immutable production delivery

After explicit authorization, production delivery uses GitHub Actions, GHCR images tagged by the full tested Git commit SHA, GitHub OIDC to AWS, Systems Manager instead of workflow SSH keys, and one Ubuntu EC2 Docker Compose host. Nginx terminates HTTPS; Next.js, FastAPI, and PostgreSQL are private services. PostgreSQL and uploads use stable named volumes. Alembic and catalogue synchronization are explicit release jobs, a backup precedes deployment, public health gates release recording, and rollback changes application images without automatically downgrading the database. The local development workflow and all deterministic product behavior remain unchanged.

## D010 — Terraform provisions infrastructure without application secrets

Terraform automates the documented AWS network, EC2/EIP, Systems Manager identities, GitHub OIDC deployment identity, and optional Route 53, budget, and GitHub environment variables. It does not accept application secrets because Terraform state and saved plans can retain managed values. The host generates the initial PostgreSQL password at boot; Gemini, private GHCR, repository deploy keys, and TLS private material remain EC2-only. Terraform state is excluded from Git and must be protected as operational data.

## D011 — Temporary DuckDNS hostname

The Phase 1 public deployment uses `certifylk.duckdns.org` pointing to the Terraform-managed Elastic IP. This avoids purchasing a domain during the AWS trial while still supporting Let's Encrypt HTTPS. DuckDNS is temporary operational infrastructure, not a product dependency; a controlled domain may replace it later by updating DNS, certificate, Nginx, GitHub environment, and EC2 environment values together.

## D012 — Immutable GitHub OIDC identity

The AWS trust policy uses GitHub's immutable owner and repository IDs in the exact production-environment subject: `repo:HirushaSipsara@127508250/certifylk@1324306736:environment:production`. Wildcard repository or branch trust is rejected. A repository transfer or replacement requires reviewing the new IDs and applying a trust-policy change before deployment.

## D013 — Exact SSM authorization and portable command boundary

GitHub's deploy role receives a customer-managed policy that allows `ssm:SendCommand` only with `AWS-RunShellScript` and the single production EC2 instance. Invocation status and cancellation remain separately authorized. Because Systems Manager executes the command list through `/bin/sh`, the wrapper uses portable `set -eu`; the repository's deployment script is explicitly invoked with Bash and may use Bash strict mode. GitHub environment identifiers are normalized and validated before AWS authentication.

## D014 — Production demonstration remains mock-first

The first public deployment intentionally uses deterministic mock AI even though Gemini was verified locally. A Gemini key may be added only to the protected EC2 environment after the mock public workflow passes. Scoring, costing, priority, expected gain, and certification wording remain deterministic and provider-independent.

## D015 — Exact-run AI transparency without new persistence

Process-analysis and evidence-analysis responses include provider and fallback status from the same successful `ai_runs` record created inside `run_with_validation`; no latest-run query or schema field is added. The frontend pauses in lightweight review states to show confirmed metadata and accessible evidence polarity/confidence. Internal retries remain unobservable during the single HTTP request and are not simulated. Response-only metadata is deliberately absent after an older response or browser refresh unless the operation is run again.

## D016 — Phase 2: Track 2 Process & System Certification

Explicitly authorized by the project owner on 2026-08-07. Phase 2 lifts the Phase 1 exclusion of ISO, HACCP, and GMP and adds a second certification track to the platform for Sri Lankan food manufacturers.

**Authorized schemes (all within Sri Lanka food manufacturing readiness scope):**
- **SLS GMP Certification** (SLSI) — Good Manufacturing Practice for any food manufacturer. Mandatory tier: `recommended`.
- **HACCP Certification** (SLSI) — Hazard Analysis & Critical Control Points. Mandatory tier: `market_required` for supermarket/export/institutional markets.
- **ISO 22000:2018 Food Safety Management** (ISO/IAF-accredited CB) — International FSMS standard. Mandatory tier: `optional` domestically, `recommended` for export markets.

**Track 2 wizard flow (authorized design):** Home → Business Profile directly (no product selection step, since GMP/HACCP/ISO 22000 are not product-specific) → AI Applicability Agent recommends applicable schemes → Assessment Hub → certificate-scoped evidence/clarification/result. The entry/profile/applicability/Hub foundation is implemented; the shared scheme-specific evaluation/result cutover remains tracked in `FULL_IMPLEMENTATION_PLAN.md`.

**Product mission unchanged:** CertifyLK remains an educational readiness tool for small Sri Lankan food manufacturers. Phase 2 does not add certification issuance, official inspection, accounts, payments, or services outside Sri Lanka.

**Content verification:** All Track 2 requirement clauses are derived from publicly available SLSI and ISO guidance. Content is flagged `content_verified=False` and accompanied by the standard disclaimer. Clause counts and descriptions are approximations pending verification against purchased standard texts.

## D017 — Certificate-specific target with an explicit transitional boundary

The database-backed `Category → Product → CertificationScheme → SchemeRequirement` model is the target source of truth. The existing global requirements/recommendations/cost catalogue and chilli-paste four-page flow remain temporarily as regression and compatibility infrastructure; they are not a sourced Fresh Fruit Cordial/SLS assessment and must not be described as completion of the redesign.

The conversion will proceed as one verified vertical slice: source review and standard versioning, scheme-scoped evidence/questions, scheme-scoped deterministic evaluation/scoring/roadmap, then a Fresh Fruit Cordial/SLS sample. Track 2 reuses that completed engine afterward. Open-ended autonomous agents remain excluded; the approved AI design is a bounded sequence of typed operations over supplied, whitelisted catalogue facts.

## D018 — Track 2 entry remains business-profile-first

Track 2 starts from the Home action, creates a guest assessment, and opens `/process-management/{assessmentId}/business-profile`. It does not require a separate scheme-selection page. The applicability operation ranks SLS GMP, SLS HACCP, and ISO 22000 after the profile is saved. This records the behavior already implemented and resolves the older proposal for `/process-management/select` in favor of D016.

## D019 — Hybrid self-assessment with optional bounded evidence review

For competition reliability, each selected-scheme evidence expectation has a controlled requirement-specific current-state response (`yes`, `partial`, `no`, or `not_sure`) sourced from the catalogue requirement. Supporting image/PDF upload is optional. The deterministic requirement engine may use self-reported answers for readiness, with explicit `self_report` provenance, while evidence completeness counts only accepted uploaded-evidence observations.

Gemini evidence review remains available but is non-blocking: one file is analyzed per call with one attempt, an eight-second per-file limit, and a twenty-second request budget by default. A failed or timed-out file receives no fabricated Mock observation; successful file results are retained and the API returns a controlled partial/unavailable state that permits continuation. This exception does not alter the normal retry/fallback policy for applicability, process, clarification, or roadmap operations.
