# Local development

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

## Troubleshooting

- **Port 5432 in use:** set `CERTIFYLK_POSTGRES_PORT=55432` before `docker compose up` and change the port in backend `DATABASE_URL` to the same value. The Compose default remains 5432.
- **Database not ready:** inspect `docker compose -f infra/local/docker-compose.yml ps` and logs; wait for the health check before migrating.
- **Migration import error:** run Alembic from `backend/` with the virtual environment active.
- **Frontend cannot reach API:** verify `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1`, backend health, and `CORS_ORIGINS`.
- **Upload rejected:** images must be JPEG/PNG/WebP and within 8 MB by default; documents must be PDF within 12 MB.
- **Gemini failure:** check the backend-only key/model and `ai_runs`; enable fallback for a safe local demo. Logs intentionally do not contain prompts or raw evidence.
- **Windows lacks Make/bash:** use the direct PowerShell commands; Docker Compose and npm/Python commands are platform independent.

`make db-down` stops local PostgreSQL without deleting its volume. Production deployment and DevOps are outside this stage.
