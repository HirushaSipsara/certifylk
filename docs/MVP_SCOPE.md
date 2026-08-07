# MVP Scope

## Phase 1 — Included

- Sri Lankan food-manufacturing readiness for SLS-related preparation.
- Guest assessments addressed by UUID, four guided pages, refresh recovery, and one-click chilli-paste sample.
- Profile/adaptive questions, five process slots, relevant evidence requests, final clarifications, and a structured result.
- PostgreSQL persistence, local filesystem uploads, mock/Gemini AI adapters, exact-run AI provider/fallback transparency, accessible evidence-observation review, deterministic scoring/roadmap/costing, responsive UI, API errors, and truthful loading states.
- Local Compose database, Alembic, seed data, tests, run scripts, and documentation.
- A separately authorized production delivery layer for the unchanged MVP: CI, immutable Docker images, single-host EC2 Compose, Nginx/HTTPS, persistent volumes, backup, and rollback.
- **Redesign (authorized 2026-08-07):** Database-backed certification knowledge base (`Category → Product → CertificationScheme → SchemeRequirement`), Track 1 Product Quality wizard (SLS Mark Fresh Fruit Cordial, CAA Food Registration), Applicability Reasoning Agent, Assessment Hub.

## Phase 2 — Included (authorized 2026-08-07, see D016)

- **Track 2: Process & System Certification** — SLS GMP Certification, HACCP Certification, ISO 22000:2018 Food Safety Management for Sri Lankan food manufacturers.
- Business-profile-first wizard flow for Track 2 (no product selection step).
- Full 4-page readiness assessment for Track 2 via existing Assessment Hub and wizard pages.

## Excluded

- Other countries, industries, and certifications outside of those documented in Phase 1 and Phase 2 above; certification issuance or guarantees; accounts/roles; administrators/auditors; payments; suppliers; official submissions; appointments; real-time monitoring; generic chat; vector databases; LangChain/agents; custom models; multi-region/high-availability infrastructure; Kubernetes; and application-managed cloud storage.

## Definition of done

The documented endpoints and pages exist, the complete mock workflow persists and returns a result, Gemini can be enabled only from the backend, catalogue/whitelist safeguards are enforced, migrations and seed data run, supported tests pass, local commands remain documented, and the same workflow can be released through the test-gated production deployment contract.

## Feature freeze

Work in Phase 1 and Phase 2 may fix correctness, accessibility, safety, documentation, or test gaps only. New product features require an explicit scope decision recorded in `DECISIONS.md` before code changes.

Production delivery is frozen to the documented single-EC2 architecture. Infrastructure changes may improve security, reliability, recovery, or testability, but may not introduce product features or change API/domain behavior.
