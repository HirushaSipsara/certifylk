# CertifyLK implementation progress

**Last reconciled:** 2026-08-07

**Status:** certificate-specific redesign in progress; infrastructure and legacy MVP operational

**Public URL recorded by operations:** <https://certifylk.duckdns.org>

**Public AI mode last recorded:** deterministic Mock

This file reports repository capability, not certification validity. A previously deployed commit may differ from the current branch. Confirm the release SHA in GitHub/EC2 before describing a new feature as live.

## Implemented

### Engineering and delivery foundation

- FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, PostgreSQL, typed services/repositories, centralized API errors, correlation IDs, and OpenAPI.
- Next.js App Router, strict TypeScript, Tailwind, React Hook Form, Zod, native API client, accessible reusable assessment/evidence/result components.
- Safe image/PDF uploads through generated filesystem keys and a `StorageProvider` boundary.
- Deterministic Mock AI and optional backend-only Gemini with structured validation, one retry, fallback control, exact-run `ai_runs` metadata, and prompt-injection boundaries.
- Deterministic legacy requirement evaluation, scoring, catalogue costing, roadmap ranking, expected gains, and projections.
- Local Compose PostgreSQL, test/check scripts, production Docker/Compose/Nginx, Terraform AWS single-host provisioning, GitHub Actions CI/CD, OIDC/SSM deployment, HTTPS, persistent volumes, backups, health checks, and rollback scripts.

### Certificate-specific redesign foundation

- Database entities and migrations for `BusinessProfile`, `Category`, `Product`, `CertificationBody`, `SourceDocument`, `CertificationScheme`, `SchemeRequirement`, `EvidenceExpectation`, and `SchemeCostItem`.
- Idempotent seed service for Food Products / Fresh Fruit Cordial, SLS Mark/CAA catalogue data, and Track 2 schemes.
- Track 1 routes: `/product-quality/select`, `/product-quality/{assessmentId}/business-profile`, and `/product-quality/{assessmentId}/certificates`.
- Track 2 routes: Home action → `/process-management/{assessmentId}/business-profile` → `/process-management/{assessmentId}/certificates`.
- API-driven scheme chips, business-profile persistence, product association for Track 1, and track inference for applicability.
- Bounded `plan_applicable_schemes` operation in Mock/Gemini provider contracts. It receives DB-sourced scheme facts, validates all returned scheme IDs, stores the decision, and returns provider/fallback metadata.
- Assessment Hub and scheme-requirement browser at `/assessment/{assessmentId}/hub` and `/hub/requirements`.
- Track 2 seeds for SLS GMP, SLS HACCP, and ISO 22000 with deterministic Mock applicability behavior and catalogue tests.
- Scheme-specific deterministic result branch for assessments with `scheme_id`: loads `scheme_requirements`, freezes scheme version/revision, uses scheme category weights, persists scheme-bound evaluations, and stores a `scheme_cost_items` roadmap snapshot.
- Bounded, Grounded AI Workflow (Phase D): Applicability, evidence analysis, clarification planning, and roadmap explanations operate strictly on DB-supplied candidate sets with strict ID whitelist validation and fallback logging. Added typed `AssessmentWorkflowCoordinator` and adversarial test suite.
- Frontend Completion for Track 1 & Track 2 (Phase E): Complete landing page, track CTAs, guest assessment recovery dashboard (`/my-assessments`), education guide (`/education`), scheme applicability cards, assessment hub, scheme-bound process page, requirement-tagged evidence upload/review page, clarification flow, readiness indicator report with print/PDF export and Track 1 -> Track 2 handoff.
- Costing and Roadmap Completion (Phase F): Categorized cost summaries by `cost_type` (`certifying_body_fee`, `lab_testing_fee`, `business_capex`, `business_opex`), non-double-counting score gain calculation, priority ordering, `quote_required` fallback flag, and frontend `CostBreakdownTable` component. Added Phase F unit & integration test suite (`test_phase_f_costing.py`).
- Samples, Testing, and Migration Safety (Phase G): Canonical Track 1 Fresh Fruit Cordial (SLS 187) sample endpoint, Track 2 domestic vs export mock scenarios, scheme engine validation suite (`test_phase_g_scheme_engine.py`), Track 1 API integration test (`test_phase_g_track1_integration.py`), Track 2 API integration test (`test_phase_g_track2_integration.py`), migration safety & seed idempotency suite (`test_phase_g_migration_safety.py`), frontend sample Vitest component test (`sample.test.tsx`), and Playwright E2E test suites (`track1-cordial.spec.ts`, `track2-process.spec.ts`).
- Release, Operations, and Validation (Phase H): Minimal public health check exposing service, version, and release_sha; operational production smoke script (`scripts/smoke_test.py`); disaster recovery restore drill (`scripts/backup_restore_drill.py`); immutable commit SHA release invariant; persistent Docker volume preservation; and operational health test suite (`test_phase_h_operations.py`).
- Evidence replacement and certificate context UX: resolved evidence slots can be removed and re-uploaded (or marked unavailable again) before analysis; scheme context is resolved from the assessment’s selected `scheme_id` on every assessment stage and is included in certificate-scoped result responses.
- Domain Pilot and Controlled Expansion (Phase I): Established pilot execution guidelines (`docs/PILOT_GUIDELINES.md`), structured discrepancy & severity register (`docs/PILOT_FEEDBACK_REGISTER.md`), and factual data governance/consent boundaries (`docs/PRIVACY_AND_CONSENT.md`). Protocol is prepared; live manufacturer sessions and domain reviewer evaluation remain pending.



## Partially implemented

| Area | What works | What remains |
|---|---|---|
| Standards knowledge base | Scheme requirements, clause/source strings, category weights, costs, source-register rows, version/revision fields, and `content_verified` exist. | Primary-source review, lawful content governance, reviewed import files, retired-date lifecycle, and domain approval. |
| Applicability reasoning | AI ranks only supplied scheme IDs and persists one recommended scheme. | A richer, auditable grounding trail/tool-call model and reviewed legal applicability facts. |
| Assessment Hub | Shows linked scheme and its requirements. | Must control the entire scheme-specific evidence → clarification → result journey. |
| Evidence | Legacy safe upload, observation polarity/confidence, provider/fallback, unavailable behavior, and seeded scheme evidence expectations work. | Full evidence-plan UI/service cutover to `evidence_expectations` and hard binding for every file/request. |
| Questions | Legacy adaptive/clarification whitelisting works. | Scheme-specific question/evaluation-rule catalogue and unresolved-requirement planning. |
| Scoring and roadmap | Legacy deterministic engines and sample baseline work; scheme assessments now use scheme requirements/weights/cost snapshots. | Richer scheme recommendation mapping, grouped fee/capex/opex result table, and frontend result polish. |
| Track 2 | Entry, profile, applicability page, seeds, service tests, and scheme-specific scoring branch exist. | Complete GMP/HACCP/ISO 22000 frontend evidence/clarification/result journeys using distinct scheme sets. |
| Sample | Legacy chilli-paste result remains deterministic. | Replace primary demo with a clearly labelled read-only Fresh Fruit Cordial/SLS sample after scheme cutover. |

## Not implemented

- Historical catalogue version entities with retired dates and reviewed import workflow.
- Full requirement-specific evidence-plan cutover in the user workflow.
- Certification-body fee versus lab fee versus business capex/opex result table.
- PDF export.
- Browser-local “My Assessments” dashboard.
- “Understand Certification” education page.
- Reviewed YAML/JSON/CSV content-import governance or admin interface.
- Domain-expert review and 2–3 manufacturer pilot.
- Verified off-host backup/restore evidence for the redesigned release.
- The referenced `sri_lanka_certification_system_complete_guide.md` is not currently present in the repository and therefore is not yet a versioned canonical source.

## Important truth statements

- The current catalogue rows are marked `content_verified=false`; clause descriptions and legal/market tiers must be verified before public reliance.
- The current applicability operation is a typed, bounded AI call over supplied facts. It should not yet be advertised as Gemini function-calling/tool execution unless that behavior is implemented and logged.
- The legacy sample score `32.0000` raw / `32` displayed protects the old deterministic engine. It is not a Fresh Fruit Cordial/SLS Mark readiness score.
- The `scheme_requirements` catalogue powers scheme-specific results when `scheme_id` is set, but the legacy `requirements` scoring catalogue still exists for the old chilli-paste regression flow.
- No result is official approval, legal advice, a laboratory result, or a certification probability.

## Completion roadmap

The authoritative remaining-work sequence and acceptance checklist are in [FULL_IMPLEMENTATION_PLAN.md](FULL_IMPLEMENTATION_PLAN.md). The immediate priorities are:

1. obtain and review primary-source Fresh Fruit Cordial/SLS content and costs;
2. replace draft source rows with reviewed import files and complete catalogue lifecycle metadata;
3. re-point evidence and questions to the assessment’s selected scheme;
4. deliver and test one Fresh Fruit Cordial/SLS vertical slice;
5. reuse the completed engine for Track 2;
6. add PDF/dashboard/education and perform production migration, restore drill, and domain pilot.

## Local verification commands

```powershell
$env:CERTIFYLK_POSTGRES_PORT = "55432"
docker compose -f infra/local/docker-compose.yml up -d

Push-Location backend
python -m alembic upgrade head
Pop-Location
python scripts/seed_demo_data.py

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

For release claims, also run the CI browser path, both production container builds, Compose validation, migrations against an upgraded database copy, and the public checklist in `RELEASE_CHECKLIST.md`.
