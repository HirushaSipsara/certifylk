# Test plan

## Backend unit tests

- Assert category weights total 100 and requirement weights total each category.
- Verify confirmed/partial/gap/unknown multipliers, distinct gap/unknown presentation, and safe not-applicable normalization.
- Verify raw Decimal storage, display rounding, completeness, non-duplicated gains, capped projections, catalogue-only costs, and stable roadmap ranking.
- Reject AI question/evidence IDs outside supplied candidates, validate malformed output/fallback, and treat prompt-injection phrases as untrusted data.
- Validate generated storage keys, traversal protection, supported MIME/extensions, image/PDF limits, and file cleanup on persistence failure.

## API integration tests

Against a test database: create and retrieve an assessment; save profile and plan adaptive questions; save five steps/answers and analyze; generate an evidence plan; upload a small fixture or mark every request unavailable; analyze; plan and answer clarifications; complete; retrieve the result; assert gap/strength/cost/disclaimer. Attempting process before profile must return 409. Validation, 404, 413, and 415 envelopes and correlation IDs are checked.

## Frontend component tests

Vitest, Testing Library, and jsdom cover conditional profile Other input, exactly five process controls and the three-step rule, evidence “I do not have this” behavior, result sections/cost/disclaimer, loading/duplicate prevention, and API validation display.

## Local end-to-end happy path

Playwright runs against local frontend/backend in mock mode. It starts at `/`, loads or enters the chilli-paste workflow, reaches the result, and verifies a numeric readiness score, at least one confirmed strength, at least one gap, an LKR cost range, and the non-certification disclaimer. The backend integration flow is also executable without a browser through `scripts/check_local.sh`.

## Failure scenarios

- Database unavailable at `/ready`.
- Invalid UUID or missing assessment.
- Refresh at every page and direct access to a future page.
- Duplicate submission and invalid state transition.
- Missing conditional Other text, fewer than three process steps, unassigned question answer.
- Oversized, unsupported, extension/MIME-mismatched, and traversal-like filename uploads.
- Unresolved evidence request before analysis.
- Gemini timeout, invalid JSON, unknown whitelisted ID, retry, fallback enabled/disabled.
- Missing catalogue price or invalid requirement configuration.
- Result requested before completion.

## Manual demo checklist

1. Start PostgreSQL, migrate/seed, backend, and frontend using documented commands.
2. Confirm landing content, single primary action, disclaimer, mobile layout, and completion-time estimate.
3. Start a blank assessment; submit one invalid profile and confirm field feedback.
4. Complete profile, observe AI loading, and see two-to-five adaptive MCQs.
5. Confirm five process inputs, enter at least three, and continue.
6. Upload a supported small image/PDF if requested; mark other slots unavailable; reject an unsupported file.
7. Confirm three-to-five clarification questions and complete.
8. Inspect separate readiness/completeness, six categories, strengths/gaps/unknowns, roadmap costs/gains/projections, and disclaimer.
9. Refresh and confirm result recovery.
10. Load the sample from landing and result pages and confirm the same completed workflow shape.

## CI and production-delivery checks

- CI repeats backend format/lint/type/test and frontend audit/lint/type/component/build gates on every pull request and main push.
- CI runs the Playwright chilli-paste happy path against real FastAPI, Next.js, PostgreSQL, Alembic, and deterministic mock AI processes.
- Both production Dockerfiles must build from clean contexts; production Compose must interpolate and validate using the example environment.
- Deployment is eligible only after successful main-branch push CI and uses the exact tested commit as both GHCR application image tags.
- Before public release, validate Nginx TLS configuration, Certbot dry-run renewal, private service port isolation, persistent volume names, pre-deploy backup hashes, explicit migration/seed completion, and application rollback without volume deletion.
- The public smoke check covers `/`, `/api/v1/health`, `/api/v1/ready`, the sample result, one strength, one gap, one LKR range, and the certification disclaimer.
- Quarterly restore drills verify both PostgreSQL and upload archives on a non-production host.
- Terraform changes run `terraform fmt -check -recursive` and `terraform validate`; provider selections remain locked in `.terraform.lock.hcl`.
- Before every Terraform apply, review the plan for the expected single EC2/EBS/EIP topology, exact OIDC subject, instance-scoped SSM permission, and absence of application secrets or unexpected paid services.
- After apply, verify SSM connectivity, encrypted EBS, IMDSv2, 80/443-only ingress, DNS/EIP alignment, protected host environment ownership, certificate issuance, GitHub environment outputs, and the unchanged public sample workflow.
