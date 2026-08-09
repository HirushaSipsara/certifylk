# Test plan

## Test strategy

Tests protect two layers during conversion:

1. the existing deterministic legacy workflow and its `32.0000 / 32` sample baseline;
2. the emerging certificate-specific catalogue/applicability/Hub and, as implemented, its complete scheme-scoped workflow.

A green legacy suite is necessary but does not prove certificate-specific completion.

## Backend unit tests

### Existing regression coverage

- Legacy category/requirement totals, status multipliers, gap-versus-unknown, not-applicable normalization, Decimal rounding, completeness, ranking, non-duplicated gains, projections, and catalogue-only costs.
- Question/evidence whitelists, exact-run AI metadata, fallback behavior, prompt injection, generated storage keys, traversal/MIME/size rules, and file cleanup.
- Catalogue listing, Track 1/Track 2 separation, seeded scheme requirement/cost counts, unverified-content flags, and deterministic Mock applicability for local/export markets.
- Source-register seeding, scheme evidence expectations, applicability version/revision freeze, scheme-bound requirement evaluations, and scheme-cost roadmap snapshots.

### Required certificate-specific coverage

- Every active scheme version has category weights and requirement sums of exactly 100.
- Assessment/product/scheme relationships are valid and cannot cross tracks/products.
- Catalogue version/source/reviewer/effective-date rules are enforced.
- Evidence expectations and observations cannot reference another scheme/version.
- Scheme evaluation uses only that scheme’s requirements and preserves gap/unknown/not-applicable semantics. Backend service coverage exists; broaden through API/browser as the frontend cutover completes.
- Scheme roadmap uses only scheme-linked costs and deterministic priority/gain math. Draft costs remain unverified until source review.
- Completed snapshots remain unchanged after a later catalogue import.

## API integration tests

### Current paths

- Create/retrieve assessment and legacy profile → process → evidence → clarification → result.
- Test-only provider concern observation persists unchanged, matches its exact `ai_runs` row, and follows existing evaluation rules.
- Categories/products/schemes/requirements endpoints return seeded data.
- Product-quality business profile links product; process-management profile resolves Track 2.
- Applicability only returns supplied schemes and exact provider/fallback metadata.
- Invalid transitions, UUIDs, upload type/size and validation use the shared envelope.

### Required end-to-end API paths

- Track 1: select Fresh Fruit Cordial → profile → applicability → choose SLS scheme/version → requirements → process/evidence → clarification → complete → source-linked result.
- Track 2 domestic: profile → GMP/HACCP/ISO decisions → selected scheme assessment → result.
- Track 2 export/supermarket: different deterministic applicability tier ordering and distinct result requirements.
- Cross-scheme question/evidence/requirement IDs return a safe validation/conflict error.
- Re-running completion is idempotent and catalogue changes do not mutate stored results.
- PDF response matches stored result/version and contains the disclaimer.

## Frontend component tests

Maintain existing profile/process/evidence/result/provider/polarity/error/loading tests. Add:

- API-driven track chips and empty/error fallback;
- category/product selection and Track 2 direct entry;
- applicability tier grouping, recommended path, source/reference expander, provider/fallback, and unverified banner;
- scheme/version requirement overview;
- requirement-tagged evidence and unavailable behavior;
- dynamic scheme categories instead of legacy fixed categories;
- grouped cost types/payers and source dates;
- My Assessments stale-link handling and PDF download state.

All state treatments require visible text/icon, keyboard access, and mobile layout coverage where supported.

## Browser E2E

Run against real FastAPI, PostgreSQL, migrations, deterministic seed, Next.js, and Mock AI:

1. Fresh Fruit Cordial/SLS canonical sample to result.
2. Manual Track 1 evidence path with at least one support/concern/unclear observation and confidence/provider label.
3. Track 2 domestic flow.
4. Track 2 export/supermarket flow, proving HACCP/ISO recommendations differ appropriately.
5. Refresh/resume at Hub/evidence/result and browser-local My Assessments when implemented.

The current chilli-paste browser test stays until the new canonical sample replaces it; then it moves to legacy regression or is retired deliberately.

## Failure and safety scenarios

- Database/catalogue unavailable or unseeded.
- No schemes for a product/track; invalid track filter; missing product/profile/scheme/version.
- Model returns unknown scheme/question/evidence/requirement/source IDs, malformed JSON, or fabricated fields.
- Gemini timeout/429/invalid response with fallback enabled and disabled, including bounded retry delay and safe diagnostics.
- Gemini transport contract proves actual image/PDF bytes and MIME types are present, requirement context is supplied, irrelevant evidence is not transformed into support, and successful batches retain Gemini provenance when a separate batch falls back.
- Evidence-analysis retry replaces existing observations rather than accumulating duplicates; accepted support changes readiness only through the existing deterministic requirement engine.
- Prompt-injection text in PDF/image metadata.
- Unsupported, oversized, signature-mismatched, traversal-like or cross-assessment uploads.
- Unverified content accidentally rendered without warning.
- Missing/invalid weight total or catalogue price.
- Catalogue update while an assessment is in progress.
- Migration failure, insufficient disk, unhealthy release, rollback, and restore.

## Manual acceptance checklist

1. Confirm Home shows both tracks from API data and the readiness disclaimer.
2. Complete Track 1 selection/profile/applicability and inspect recommended-path grounding.
3. Confirm the Hub shows the selected scheme/version and unverified/verified state.
4. Inspect only that scheme’s requirements, sources and clauses.
5. Upload supported synthetic evidence, mark one unavailable, and reject an invalid file.
6. Confirm observation polarity, confidence, provider/fallback and source context.
7. Complete clarification/result and inspect status separation, scheme categories, grouped costs, gains, projections and disclaimer.
8. Export the PDF and compare it to the stored UI result.
9. Complete Track 2 domestic and export cases and confirm distinct recommendations/requirements.
10. Refresh/resume and verify no credentials, prompts, raw evidence or internal errors are exposed.

## CI and release gates

- Backend Ruff, mypy, pytest, audit and Bandit.
- Frontend audit, ESLint, TypeScript, Vitest and production build.
- PostgreSQL browser E2E with Mock AI.
- Alembic upgrade from empty and production-like previous schema plus idempotent seed/import.
- Terraform formatting/validation, clean production image builds and Compose interpolation.
- Pre-deploy backup, immutable tested SHA, explicit migration/import, public HTTPS health and workflow smoke, rollback without volume deletion.
- Periodic off-host backup/restore rehearsal.

No failing or skipped critical gate may be bypassed to deploy.
