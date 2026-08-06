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

## D008 — Production/DevOps deferred during local MVP construction

CI/CD, GitHub Actions, AWS, EC2, Nginx, and production Docker deployment were explicitly deferred until the local product was accepted. This historical constraint protected the local vertical slice and is superseded for infrastructure work by D009; the product exclusions remain unchanged.

## D009 — Single-host, immutable production delivery

After explicit authorization, production delivery uses GitHub Actions, GHCR images tagged by the full tested Git commit SHA, GitHub OIDC to AWS, Systems Manager instead of workflow SSH keys, and one Ubuntu EC2 Docker Compose host. Nginx terminates HTTPS; Next.js, FastAPI, and PostgreSQL are private services. PostgreSQL and uploads use stable named volumes. Alembic and catalogue synchronization are explicit release jobs, a backup precedes deployment, public health gates release recording, and rollback changes application images without automatically downgrading the database. The local development workflow and all deterministic product behavior remain unchanged.

## D010 — Terraform provisions infrastructure without application secrets

Terraform automates the documented AWS network, EC2/EIP, Systems Manager identities, GitHub OIDC deployment identity, and optional Route 53, budget, and GitHub environment variables. It does not accept application secrets because Terraform state and saved plans can retain managed values. The host generates the initial PostgreSQL password at boot; Gemini, private GHCR, repository deploy keys, and TLS private material remain EC2-only. Terraform state is excluded from Git and must be protected as operational data.

## D011 — Temporary DuckDNS hostname

The Phase 1 public deployment uses `certifylk.duckdns.org` pointing to the Terraform-managed Elastic IP. This avoids purchasing a domain during the AWS trial while still supporting Let's Encrypt HTTPS. DuckDNS is temporary operational infrastructure, not a product dependency; a controlled domain may replace it later by updating DNS, certificate, Nginx, GitHub environment, and EC2 environment values together.

## D012 — Immutable GitHub OIDC identity

The AWS trust policy uses GitHub's immutable owner and repository IDs in the exact production-environment subject: `repo:HirushaSipsara@127508250/certifylk@1324306736:environment:production`. Wildcard repository or branch trust is rejected. A repository transfer or replacement requires reviewing the new IDs and applying a trust-policy change before deployment.

## D013 — Exact SSM authorization and portable command boundary

GitHub's deploy role receives a customer-managed policy that allows `ssm:SendCommand` only with `AWS-RunShellScript` and the single production EC2 instance. Invocation status and cancellation remain separately authorized. Because Systems Manager executes the command list through `/bin/sh`, the wrapper uses portable `set -eu`; the repository's deployment script is explicitly invoked with Bash and may use Bash strict mode. GitHub environment identifiers are normalized and validated before AWS authentication.

## D014 — Production demonstration remains mock-first

The first public deployment intentionally uses deterministic mock AI even though Gemini was verified locally. A Gemini key may be added only to the protected EC2 environment after the mock public workflow passes. Scoring, costing, priority, expected gain, and certification wording remain deterministic and provider-independent.

## D015 — Exact-run AI transparency without new persistence

Process-analysis and evidence-analysis responses include provider and fallback status from the same successful `ai_runs` record created inside `run_with_validation`; no latest-run query or schema field is added. The frontend pauses in lightweight review states to show confirmed metadata and accessible evidence polarity/confidence. Internal retries remain unobservable during the single HTTP request and are not simulated. Response-only metadata is deliberately absent after an older response or browser refresh unless the operation is run again.
