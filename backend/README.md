# CertifyLK backend

FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, PostgreSQL, generated-key storage, deterministic domain engines, and Mock/Gemini AI adapters.

The backend currently contains both the original global assessment engine and the newer certificate knowledge base/applicability layer. The required cutover is documented in `../docs/FULL_IMPLEMENTATION_PLAN.md`; do not describe the result engine as scheme-specific until it reads the selected frozen scheme requirements and costs.

## Run

```bash
python -m pip install -e ".[dev]"
copy .env.example .env
alembic upgrade head
python ../scripts/seed_demo_data.py
uvicorn app.main:app --reload --port 8000
```

OpenAPI: <http://localhost:8000/docs>. Current API contracts are in `../docs/API_CONTRACT.md`.

## Main boundaries

- `app/api/v1/`: HTTP routes and response translation.
- `app/services/`: workflows, including catalogue/applicability and legacy assessment services.
- `app/models/` and `app/schemas/`: separate ORM and Pydantic types.
- `app/ai/`: typed Mock/Gemini providers and structured prompts.
- `app/storage/`: generated-key local storage and future S3-shaped interface.
- `app/services/seed_service.py`: idempotent legacy and certificate-catalogue synchronization.

## AI provider

Mock is deterministic and keyless. Gemini is backend only:

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=your_backend_only_key
GEMINI_MODEL=gemini-3.6-flash
ALLOW_AI_FALLBACK=true
```

Run `python ../scripts/check_gemini.py` for structured connectivity. Never put the key in frontend variables or commit `.env`.

## Checks

```bash
python -m ruff format --no-cache --check app tests
python -m ruff check --no-cache app tests
python -m mypy app
python -m pytest
```
