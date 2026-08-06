# Integrated AI implementation

The AI implementation is part of the existing FastAPI backend monolith. The frontend
continues to call the same `/api/v1` endpoints and no separate AI microservice is used.

## Runtime flow

1. `profile_service` sends the saved profile and approved candidate question IDs to the
   configured `AIProvider`.
2. `process_service` sends the five process steps and adaptive answers, validates that
   every non-empty step is mapped once, and persists only approved process tags.
3. `process_service` creates the existing deterministic evidence plan.
4. `evidence_service` sends only uploaded files to the provider, validates every returned
   observation against the exact request-to-requirement mapping, and stores cautious
   observations.
5. `evidence_service` asks the provider to select approved clarification IDs.
6. `result_service` performs deterministic requirement evaluation, scoring, costing,
   ranking, expected-gain calculation, and projections. AI only explains the already
   fixed roadmap items.

## Provider selection

Use deterministic mode for development and guaranteed demos:

```env
AI_PROVIDER=mock
ALLOW_AI_FALLBACK=true
```

Use Gemini inside the backend only:

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=replace_with_backend_only_key
GEMINI_MODEL=gemini-3.6-flash
GEMINI_TIMEOUT_SECONDS=30
GEMINI_TEMPERATURE=0.1
GEMINI_MAX_OUTPUT_TOKENS=2048
ALLOW_AI_FALLBACK=true
```

Run a small structured-output connectivity check from the repository root:

```bash
python scripts/check_gemini.py
```

## Files that implement AI

- `backend/app/ai/base.py`: provider contract.
- `backend/app/ai/gemini.py`: live multimodal Gemini adapter.
- `backend/app/ai/mock.py`: deterministic fallback and demo provider.
- `backend/app/ai/prompts.py`: fixed system/task instructions.
- `backend/app/schemas/ai.py`: structured output models and text sanitization.
- `backend/app/services/ai_service.py`: retries, fallback, run logging, and whitelist
  validation.
- `backend/app/services/profile_service.py`: adaptive question operation.
- `backend/app/services/process_service.py`: process extraction operation.
- `backend/app/services/evidence_service.py`: image/PDF observation and clarification
  operations.
- `backend/app/services/result_service.py`: roadmap explanation operation after
  deterministic calculation.

No API key is included in the repository. `backend/.env` remains ignored by Git.
