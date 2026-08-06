# CertifyLK backend

FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, PostgreSQL, local storage, and Mock/Gemini AI adapters.

```bash
python -m pip install -e ".[dev]"
copy .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
pytest
```

Run `python ../scripts/seed_demo_data.py` after migration. See root `docs/` for the canonical contracts.

## AI provider mode

The complete AI implementation is part of this backend monolith under `app/ai/` and
`app/services/`. No separate AI service is required.

For deterministic local/demo behavior, keep `AI_PROVIDER=mock`. For live Gemini:

```bash
# backend/.env
AI_PROVIDER=gemini
GEMINI_API_KEY=your_backend_only_key
GEMINI_MODEL=gemini-3.6-flash
ALLOW_AI_FALLBACK=true

python ../scripts/check_gemini.py
```

Never place the Gemini key in the frontend environment or commit `backend/.env`.

