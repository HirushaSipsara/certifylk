# Phase 1 MVP scope

## Included

- Sri Lankan food-manufacturing readiness for SLS-related preparation.
- Guest assessments addressed by UUID, four guided pages, refresh recovery, and one-click chilli-paste sample.
- Profile/adaptive questions, five process slots, relevant evidence requests, final clarifications, and a structured result.
- PostgreSQL persistence, local filesystem uploads, mock/Gemini AI adapters, deterministic scoring/roadmap/costing, responsive UI, API errors, and loading states.
- Local Compose database, Alembic, seed data, tests, run scripts, and documentation.

## Excluded

Other countries, industries, and certifications; certification issuance or guarantees; accounts/roles; administrators/auditors; payments; suppliers; official submissions; appointments; real-time monitoring; generic chat; vector databases; LangChain/agents; custom models; production infrastructure.

## Definition of done

The documented endpoints and pages exist, the complete mock workflow persists and returns a result, Gemini can be enabled only from the backend, catalogue/whitelist safeguards are enforced, migrations and seed data run, supported tests pass, and local commands are documented.

## Feature freeze

Work in Phase 1 may fix correctness, accessibility, safety, documentation, or test gaps only. New product features require an explicit scope decision recorded in `DECISIONS.md` before code changes.

DevOps—including CI/CD, AWS, EC2, Nginx, production containers, and GitHub Actions—is a later stage and must not be added now.
