# Local development

This environment runs both the legacy regression workflow and the in-progress certificate-specific catalogue/applicability flows. Seed before testing either track. The authoritative remaining work is in `FULL_IMPLEMENTATION_PLAN.md`.

## Prerequisites

- Python 3.10 or newer and `pip`
- Node.js 20 or newer and npm
- Docker Desktop/Engine with Compose v2
- GNU Make for convenience (optional; direct commands are below)

PostgreSQL uses local port 5432, FastAPI 8000, and Next.js 3000.

## Environment setup

PowerShell:

```powershell
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env.local
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e "backend[dev]"
Set-Location frontend; npm install; Set-Location ..
```

Bash:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
python -m venv .venv
source .venv/bin/activate
pip install -e 'backend[dev]'
(cd frontend && npm install)
```

Or run `make install` after copying environments.

## Database and seed

```bash
make db-up
make migrate
make seed
```

Direct equivalents:

```bash
docker compose -f infra/local/docker-compose.yml up -d
cd backend && alembic upgrade head
cd .. && python scripts/seed_demo_data.py
```

`seed_demo_data.py` is idempotent. `scripts/reset_local_db.sh` asks for confirmation, recreates only the named local Compose volume/database, migrates, and seeds.

## Start applications

Terminal 1:

```bash
make backend-dev
# direct: cd backend && uvicorn app.main:app --reload --port 8000
```

Terminal 2:

```bash
make frontend-dev
# direct: cd frontend && npm run dev
```

Open <http://localhost:3000>; API docs are at <http://localhost:8000/docs>.

Useful current routes:

- `/product-quality/select` — Track 1 category/product entry;
- Home → `/process-management/{assessmentId}/business-profile` — Track 2 direct entry;
- `/assessment/{assessmentId}/hub` — linked scheme and Assessment Hub;
- `/assessment/{assessmentId}/hub/requirements` — scheme requirement overview.

There is no `/process-management/select` route.

## Tests and checks

```bash
make test
make check
```

Direct commands:

```bash
cd backend
pytest
ruff format --check app tests
ruff check app tests
mypy app
cd ../frontend
npm test -- --run
npm run lint
npm run typecheck
npm run build
```

For the HTTP happy path while the services run: `bash scripts/check_local.sh`.

The current browser happy path primarily protects the legacy chilli-paste workflow. Also manually verify both track entry/profile/applicability pages until the new automated Track 1 and Track 2 paths in `TEST_PLAN.md` are implemented.

## AI modes

Mock mode is the default and requires no key:

```env
AI_PROVIDER=mock
ALLOW_AI_FALLBACK=true
```

Gemini mode uses backend `.env` only:

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=your-key
GEMINI_MODEL=gemini-3.6-flash
ALLOW_AI_FALLBACK=true
```

Restart FastAPI after changes. Never add these variables to `frontend/.env.local` or prefix a secret with `NEXT_PUBLIC_`.

Mock provider labels are visible automatically in development and tests. To exercise that label in a production-mode QA build, set this non-secret frontend flag before building:

```env
NEXT_PUBLIC_SHOW_MOCK_AI_STATUS=true
```

Normal production builds may leave it false. Gemini and confirmed fallback labels are driven only by API response metadata; this flag never selects an AI provider.

## Troubleshooting

- **Port 5432 in use:** set `CERTIFYLK_POSTGRES_PORT=55432` before `docker compose up` and change the port in backend `DATABASE_URL` to the same value. The Compose default remains 5432.
- **Database not ready:** inspect `docker compose -f infra/local/docker-compose.yml ps` and logs; wait for the health check before migrating.
- **Migration import error:** run Alembic from `backend/` with the virtual environment active.
- **Frontend cannot reach API:** verify `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1`, backend health, and `CORS_ORIGINS`.
- **Upload rejected:** images must be JPEG/PNG/WebP and within 8 MB by default; documents must be PDF within 12 MB.
- **Gemini failure:** check the backend-only key/model and `ai_runs`; enable fallback for a safe local demo. Logs intentionally do not contain prompts or raw evidence.
- **Windows lacks Make/bash:** use the direct PowerShell commands; Docker Compose and npm/Python commands are platform independent.

`make db-down` stops local PostgreSQL without deleting its volume. The production files do not replace or alter this local workflow; see `PRODUCTION_DEPLOYMENT.md` only when operating the separate production stage.
