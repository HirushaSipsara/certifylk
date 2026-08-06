# Phase 1 MVP scope

## Included

- Sri Lankan food-manufacturing readiness for SLS-related preparation.
- Guest assessments addressed by UUID, four guided pages, refresh recovery, and one-click chilli-paste sample.
- Profile/adaptive questions, five process slots, relevant evidence requests, final clarifications, and a structured result.
- PostgreSQL persistence, local filesystem uploads, mock/Gemini AI adapters, exact-run AI provider/fallback transparency, accessible evidence-observation review, deterministic scoring/roadmap/costing, responsive UI, API errors, and truthful loading states.
- Local Compose database, Alembic, seed data, tests, run scripts, and documentation.
- A separately authorized production delivery layer for the unchanged MVP: CI, immutable Docker images, single-host EC2 Compose, Nginx/HTTPS, persistent volumes, backup, and rollback.

## Excluded

Other countries, industries, and certifications; certification issuance or guarantees; accounts/roles; administrators/auditors; payments; suppliers; official submissions; appointments; real-time monitoring; generic chat; vector databases; LangChain/agents; custom models; multi-region/high-availability infrastructure; Kubernetes; and application-managed cloud storage.

## Definition of done

The documented endpoints and pages exist, the complete mock workflow persists and returns a result, Gemini can be enabled only from the backend, catalogue/whitelist safeguards are enforced, migrations and seed data run, supported tests pass, local commands remain documented, and the same workflow can be released through the test-gated production deployment contract.

## Feature freeze

Work in Phase 1 may fix correctness, accessibility, safety, documentation, or test gaps only. New product features require an explicit scope decision recorded in `DECISIONS.md` before code changes.

Production delivery is frozen to the documented single-EC2 architecture. Infrastructure changes may improve security, reliability, recovery, or testability, but may not introduce product features or change API/domain behavior.
