# Architecture decision log

## D001 — Guided workflow, not chat

Phase 1 uses four fixed assessment pages. This keeps evidence collection predictable, supports validation, and matches the locked buildathon workflow.

## D002 — Deterministic domain decisions

Requirements, statuses, readiness, completeness, priorities, gains, projections, and costs are calculated in Python using versioned seed data. AI is restricted to extraction, selection, and explanation.

## D003 — Guest UUID state

There is no authentication. The assessment UUID is persisted in the URL/local storage and is the local resume token. This is suitable for the local MVP only.

## D004 — PostgreSQL and JSONB

Normalized entities retain auditable workflow data; JSONB holds bounded, versioned payloads such as option arrays, applicability tags, evaluation evidence references, and result snapshots.

## D005 — Local storage abstraction

Uploads use generated keys beneath a configured local root. An S3-shaped class exists only to preserve the interface boundary; AWS calls are excluded.

## D006 — Mock-first provider

Mock AI is the default for reproducible local development and tests. Gemini is opt-in with backend-only credentials, one retry, structured validation, and configurable fallback.

## D007 — Complete sample endpoint

The sample endpoint creates a new, completed chilli-paste assessment by exercising the same persistence, evaluation, scoring, and roadmap services used by manual completion. It avoids external network calls for a reliable demo.

## D008 — No production/DevOps work

CI/CD, GitHub Actions, AWS, EC2, Nginx, and production Docker deployment remain explicitly deferred until the local product is accepted.
