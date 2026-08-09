# AI integration

AI remains inside the FastAPI monolith behind `AIProvider`; there is no AI microservice, chatbot, LangChain runtime, or autonomous agent process.

## Implemented flow

1. `catalog_service` selects active schemes for the product/track from PostgreSQL.
2. `applicability_service` supplies business/product and candidate scheme facts to `plan_applicable_schemes`, enforces the ID whitelist, persists the decision, and links the recommended scheme.
3. Legacy `profile_service`, `process_service`, and `evidence_service` plan questions, normalize five process steps, create evidence requests, and store validated observations.
4. `result_service` uses a scheme-specific deterministic branch when `assessment.scheme_id` is set, loading `scheme_requirements`, scheme category weights, and `scheme_cost_items`; legacy assessments without `scheme_id` continue through the global regression catalogue.
5. `ai_service.run_with_validation` records exact-run success/provider/fallback metadata.

For the hybrid evidence stage, each database evidence expectation exposes one controlled self-assessment answer (`yes`, `partial`, `no`, or `not_sure`) and an optional upload. Self-assessment is deterministic input to the requirement engine and is tagged `self_report`; it is not evidence. `evidence_service` reopens each uploaded file from the configured storage provider and sends its actual bytes and MIME type to Gemini as multimodal inline data. Requests are sequential and contain one file. Every call validates the exact request/requirement pair independently. Evidence review uses one attempt, no Mock substitution, an eight-second per-file timeout, and a twenty-second total request budget by default. Successful Gemini observations are retained; failed files remain uploaded and return a controlled partial/unavailable response. Observation rows persist `provider`, `fallback_used`, and `validation_status` for the exact call that produced them.

The important current limitation is now earlier in the workflow: question and evidence planning still need full cutover to the assessment’s frozen scheme version before describing the browser journey as certificate-specific end to end.

## Target bounded workflow

```text
business/product profile
  → supplied catalogue applicability decision
  → selected and frozen scheme/version
  → scheme requirement/evidence planning
  → requirement-bound evidence extraction
  → unresolved whitelisted clarifications
  → deterministic evaluation/scoring/roadmap/cost
  → AI narrative over the fixed result
```

A typed application coordinator may sequence these operations. It has fixed steps and state transitions; the model cannot choose arbitrary tools/actions. Optional Gemini function calling, if implemented, is restricted to read-only catalogue lookup functions returning bounded rows.

## Implementation files

- `backend/app/ai/base.py` — provider protocol.
- `backend/app/ai/mock.py` — deterministic provider, including Track 1/Track 2 applicability.
- `backend/app/ai/gemini.py` — live structured-output adapter.
- `backend/app/ai/prompts.py` — fixed safety/task instructions.
- `backend/app/schemas/ai.py` — validated output schemas and sanitization.
- `backend/app/services/ai_service.py` — provider selection, retry/fallback, validation and `ai_runs`.
- `backend/app/services/applicability_service.py` — DB-grounded scheme decision and persistence.
- `backend/app/services/catalog_service.py` — category/product/scheme/requirement queries.
- `backend/app/services/profile_service.py`, `process_service.py`, `evidence_service.py` — legacy workflow services being re-plumbed.
- `backend/app/services/result_service.py` — legacy result branch plus scheme-specific deterministic result branch.

## Provider configuration

Deterministic development/demo:

```env
AI_PROVIDER=mock
ALLOW_AI_FALLBACK=true
```

Gemini, backend only:

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=replace_with_backend_only_key
GEMINI_MODEL=gemini-3.6-flash
GEMINI_TIMEOUT_SECONDS=30
GEMINI_TEMPERATURE=0.1
GEMINI_MAX_OUTPUT_TOKENS=2048
ALLOW_AI_FALLBACK=true
EVIDENCE_AI_TIMEOUT_SECONDS=8
EVIDENCE_AI_TOTAL_TIMEOUT_SECONDS=20
```

Run `python scripts/check_gemini.py` from the repository root for structured connectivity. Never place the key in the frontend or commit `backend/.env`.

## Required completion tests

- Track candidates cannot cross between product-quality and process-management.
- Unknown scheme/question/evidence/requirement IDs fail before domain persistence.
- Prompt-injection evidence remains data.
- An observation cannot reference a different scheme’s requirement.
- Provider/fallback metadata belongs to the exact run.
- Mock/Gemini output cannot change legal tier facts, weight, status multiplier, priority, cost, gain, or projection.
- A catalogue version change does not alter a completed result snapshot.
