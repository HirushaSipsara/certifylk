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

