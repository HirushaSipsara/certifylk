# CertifyLK full implementation plan

**Plan date:** 2026-08-09
**Purpose:** complete the approved conversion from a generic readiness quiz to a sourced, product-and-certificate-specific guidance system without discarding the working FastAPI, Next.js, AI, evidence, deterministic-engine, test, and deployment foundations.

## 1. Definition of the finished product

For the authorized scope, CertifyLK is complete when a Sri Lankan food manufacturer can enter through Product Quality or Process & System, receive a source-grounded AI applicability recommendation, start one assessment for one scheme, review the exact requirement set and its verification status, submit evidence, answer only unresolved questions, and receive a deterministic clause-linked readiness result and cost roadmap. The entire path must work in Mock and Gemini modes, locally and through the existing production delivery pipeline.

“Complete” does not mean official certification. It does not include accounts, payments, official submissions, other industries/countries, or schemes beyond the authorized catalogue.

## 2. Verified implementation position

| Capability | Current state | Completion gap |
|---|---|---|
| FastAPI/Next.js/PostgreSQL foundation | Implemented | Maintain and extend; do not rewrite. |
| AWS/Terraform/CI/CD/Nginx/HTTPS | Implemented single-host design | Re-run current release gates after product changes; improve off-host backups separately. |
| Category/product/body/scheme/requirement/cost tables | Implemented | Replace draft source rows with reviewed import files and add retired-date lifecycle. |
| Track 1 entry and assessment | Implemented for Food Products / Fresh Fruit Cordial | Verify all content and evidence questions against primary sources and pilot with users. |
| Track 2 entry and assessment | Implemented as home → business profile → certificates → shared assessment journey | Verify GMP/HACCP/ISO 22000 content against licensed/primary sources and pilot. |
| Applicability AI | Implemented as a bounded operation over DB-supplied scheme facts with ID validation | Add explicit grounding/reference trail and automated ambiguity tests; do not claim tool calls that are not yet implemented. |
| Assessment Hub / requirements browser | Implemented | Maintain it as the controlling entry to certificate-specific process, evidence, clarification, result, and roadmap. |
| Legacy four-page assessment | Implemented and tested | Retain only as regression/sample until replacement; it still evaluates the generic `requirements` catalogue. |
| Scheme-specific deterministic evaluation | Implemented end to end | Maintain cross-scheme isolation; legacy branch remains for chilli-paste regression. |
| Hybrid requirement self-assessment / optional evidence | Implemented | Verify production Gemini capability/quota per release and validate questions with a domain reviewer. |
| Certificate-specific cost table | Integrated in scheme result snapshot and grouped UI | Replace unverified figures with reviewed source data. |
| PDF/print export | Implemented from stored result UI | Continue stored-result parity checks. |
| My Assessments / education page | Implemented | Keep guest-storage and source/disclaimer wording explicit. |
| Admin/content management | Not implemented | Start with reviewed version-controlled YAML/JSON/CSV import; UI is later and separately authorized. |
| Primary-source/domain review | Not complete | This is the main release blocker for trustworthy public guidance. |

## 3. Workstreams and dependency order

### Phase A — Content authority and governance (P0, do first)

1. Obtain or lawfully access the applicable SLS Fresh Fruit Cordial specification, current SLS Mark procedure, relevant Food Act/labelling material, SLS GMP/HACCP guidance, and licensed ISO 22000:2018 material.
2. Add the referenced `sri_lanka_certification_system_complete_guide.md` to the reviewed documentation/source workflow if it is intended to be canonical; it is not currently present in this repository.
3. Have a qualified reviewer approve interpretations. Do not copy copyrighted standards wholesale; store concise implementation-oriented summaries and clause references.
4. Create a source register containing document title, owner/body, edition/version, effective date, source URL or purchase reference, access date, copyright constraint, reviewer, review date, and verification state.
5. Verify whether each pathway is legally mandatory, market-required, recommended, or optional for each supported market. Treat SLS Mark as market-required unless a primary legal source proves a mandatory case.
6. Obtain written/published fee schedules or dated quotes for certification, audit, laboratory, training, and common business improvements.
7. Keep `content_verified=false` and the visible warning until review is complete.

**Current software status:** source-register rows exist and all seeded draft content remains visibly unverified.

**Exit criteria:** every active catalogue fact has a reviewed source record and reviewer; unsupported claims are removed or visibly unverified; no invented threshold or price is displayed.

### Phase B — Versioned certification knowledge base (P0)

1. Add scheme/requirement version and effective-date fields or immutable version entities so old assessments retain the rules used at completion.
2. Add a curated evidence-type/evidence-expectation table tied to scheme requirements (`photo`, `document`, `lab_report`, `licence`, `declaration`) with user guidance.
3. Add assessment binding to the exact scheme version/catalogue revision.
4. Decide whether the existing legacy `requirements`, `recommendations`, and `cost_items` tables remain during migration or are converted. Do not maintain two active sources of truth after cutover.
5. Move source data into reviewed, version-controlled import files and make synchronization idempotent and auditable. A seed/import workflow is the initial content-management interface.
6. Add uniqueness, foreign keys, indexes, and Alembic migration(s); update `DATA_MODEL.md` in the same commit.

**Current software status:** assessments/results can freeze selected scheme version and catalogue revision; historical retired-date/version entities and reviewed import files remain.

**Exit criteria:** a completed assessment can always reproduce its requirement and cost basis even after a catalogue update.

### Phase C — Certificate-scoped assessment domain (P0)

1. Require a selected `scheme_id` and the frozen scheme version before entering evidence/evaluation. Product is required only for product-specific schemes.
2. Change requirement loading from the global catalogue to the assessment’s scheme requirement set.
3. Build candidate questions from each scheme requirement’s reviewed `evaluation_rule`; reject legacy/global question mappings that do not belong to the selected scheme.
4. Build the evidence plan from curated scheme evidence expectations and applicable process/profile facts.
5. Bind every evidence request, file, observation, clarification, evaluation, recommendation, and cost snapshot to the assessment and selected scheme requirements.
6. Preserve the existing status semantics and deterministic multipliers. Normalize category weights safely per scheme.
7. Make completion transactional and idempotent. Prevent cross-scheme evidence or question IDs.
8. Keep the legacy chilli-paste sample isolated as a regression fixture until a new read-only Fresh Fruit Cordial/SLS sample is complete; then remove it from the primary home path.

**Current software status:** selected-scheme requirements, evidence expectations, controlled self-assessment, optional uploads, evaluations, category weights, and costs drive the shared journey. Legacy chilli-paste data remains isolated for regression only.

**Exit criteria:** changing the selected scheme changes the requirements/questions/evidence/result, and tests prove no data can leak between schemes.

### Phase D — Bounded, grounded AI workflow (P0)

1. Keep `AIProvider` and `run_with_validation`; add no free-form chatbot or open-ended autonomous agent.
2. Applicability must receive only DB-sourced product, profile, scheme, legal-tier, and source facts. It returns ranked whitelisted scheme IDs, reasoning, confidence, and references to supplied facts.
3. If actual Gemini function/tool calling is adopted, expose a fixed tool registry such as `get_applicable_laws`, `get_certification_schemes`, `get_applicability_rule`, and `get_market_requirements`; tools are read-only and return bounded rows. Otherwise describe the current supplied-context operation honestly.
4. Optional evidence analysis receives one uploaded file plus the selected requirement and retrieved threshold/evaluation data. It returns extracted observations, not official pass/fail certification conclusions. Short bounded failure returns a continuable unavailable state and never fabricates a positive/fallback observation.
5. Clarification planning considers already resolved requirements and selects only supplied question IDs.
6. Roadmap narration receives the immutable deterministic roadmap and source references and may not create actions, prices, gains, priorities, or clauses.
7. Add a typed workflow coordinator to sequence these bounded operations and persist step state. It is an application service, not a self-directing autonomous agent.
8. Preserve exact-run provider/fallback metadata and add grounded-source display metadata only when it can be truthfully tied to the current run.

**Exit criteria:** tests inject unknown IDs, fake clauses, fake costs, prompt injection, and cross-requirement references and prove all are rejected without changing deterministic state.

### Phase E — Frontend completion (P0/P1)

1. Finish Home with API-driven chips, two clear track actions, About/What We Offer, education link, and an explicitly read-only Fresh Fruit Cordial/SLS example.
2. Keep Track 1 category/product selection and Track 2 direct business-profile entry. Do not add a `/process-management/select` route unless a later decision changes D016.
3. Improve applicability cards: grouped tiers, one recommended path, issuing body, timeline, AI provider/fallback, confidence, “Why this?”, source reference, and unverified-content banner.
4. Make the Assessment Hub show the selected product/scheme/version and five target stages: requirements, evidence/process, clarification, result, roadmap/report.
5. Keep requirement-tagged controlled current-state answers, optional upload controls, and `I do not have this evidence` for every requested item.
6. Reuse accessible evidence polarity/confidence components and show clause/source context beside observations.
7. Render scheme-specific categories/statuses, costs grouped by payer/type, expected gains, and cumulative projection.
8. Add PDF export generated from stored result data; include timestamp, catalogue version, sources, verification warnings, and disclaimer.
9. Add “My Assessments” using locally remembered UUIDs. Label it as browser-local guest recovery, not an authenticated private account.
10. Add “Understand Certification” using reviewed summaries from the research guide; do not publish unsupported legal claims.

**Exit criteria:** both tracks pass mobile/keyboard/manual and Playwright journeys from landing to a source-linked result.

### Phase F — Costing and roadmap completion (P0)

1. Map each scheme gap/unknown to reviewed `scheme_cost_items` or a scheme-scoped recommendation catalogue.
2. Separate certification-body fee, laboratory fee, business capex, and business opex in the API and UI.
3. Store min/max, recurrence period, currency, source note, effective date, last reviewed date, and whether tax/travel/consultancy is excluded.
4. Derive expected gain only from uncovered applicable requirement weight; prevent double counting exactly as the current deterministic engine does.
5. Preserve stable priority ordering: safety-critical, high weight, low-cost/high-gain, documentation, then capital expense.
6. When no verified price exists, display “quote required” or omit the amount; never ask AI to estimate it.

**Exit criteria:** every displayed numeric cost is traceable to an active reviewed catalogue row and the completed result snapshots it.

### Phase G — Samples, testing, and migration safety (P0)

1. Create a canonical Fresh Fruit Cordial/SLS sample that uses the new APIs and scheme-specific engine; include at least two strengths, gaps, unknowns, evidence polarity, costs, and disclaimer.
2. Add Track 2 Mock journeys for a local-retail case and an export/supermarket case, verifying different GMP/HACCP/ISO recommendations.
3. Add unit tests for per-scheme weight totals, not-applicable normalization, catalogue versions, source verification, costs, ranking, and cross-scheme isolation.
4. Add API integration tests for both track entry flows, business profile, applicability, scheme selection, requirements, evidence, clarifications, completion, and result.
5. Add frontend component and Playwright tests for tier grouping, source banners, scheme-specific requirements, grouped costs, and report export.
6. Preserve the legacy `32.0000 / 32` chilli-paste score only as a regression baseline while legacy code remains. Do not use it as the new SLS Cordial score.
7. Test migration from a production-like database backup, idempotent catalogue synchronization, rollback compatibility, and preservation of completed snapshots.

**Exit criteria:** `make check`, container builds, production Compose validation, migrations against empty and upgraded databases, and both browser tracks pass for the exact release SHA.

### Phase H — Release, operations, and validation (P1)

1. Update public health/smoke checks to cover catalogue loading, both entry tracks, one complete scheme assessment, and the certification disclaimer.
2. Back up production before migration; never delete named PostgreSQL/upload volumes.
3. Deploy immutable commit-SHA images through the existing GitHub OIDC/SSM pipeline only after CI passes.
4. Keep Mock as the deterministic public-demo fallback. Enable Gemini only through the protected EC2 backend environment and re-run evidence/applicability manual checks.
5. Export encrypted off-host backups and complete a restore drill.
6. Add monitoring for disk, container health, certificate renewal, backup age, error rate, and AI failure/fallback rate without logging evidence content.

**Exit criteria:** a production smoke run completes both tracks using synthetic/non-sensitive data, HTTPS is valid, rollback is proven, and restore evidence is recorded.

### Phase I — Domain pilot and controlled expansion (P1/P2)

1. Pilot with 2–3 Fresh Fruit Cordial manufacturers and a qualified certification/food-safety reviewer.
2. Compare applicability and gap output with professional review; record false positives, false negatives, unclear evidence, and language comprehension issues.
3. Correct only source data/evaluation mappings through reviewed catalogue versions; never tune AI to hide disagreements.
4. Complete privacy/retention consent review before accepting real production evidence on the AWS trial environment.
5. Add a second product or another scheme only after a new scope decision, source pack, reviewer, costs, tests, and UI copy are ready.

## 4. Recommended delivery slices

| Slice | Deliverable | Priority | Depends on |
|---|---|---:|---|
| 1 | Source register + reviewed Fresh Fruit Cordial/SLS content pack | P0 | Domain documents/reviewer |
| 2 | Versioned schema + evidence expectations + migrations/import | P0 | Slice 1 data shape |
| 3 | Scheme-scoped requirement/evidence/evaluation/scoring services | P0 | Slice 2 |
| 4 | Fresh Fruit Cordial/SLS end-to-end UI and sample | P0 | Slice 3 |
| 5 | Scheme costs + grouped roadmap + PDF | P0/P1 | Slices 1–4 |
| 6 | GMP/HACCP/ISO 22000 end-to-end assessments | P0 | Slices 2–4 and verified Track 2 content |
| 7 | AI grounding trail and bounded workflow coordinator | P1 | Stable domain contracts |
| 8 | Dashboard, education, accessibility polish | P1 | Stable routes/results |
| 9 | Production migration, smoke, restore, pilot | P1 | All release gates |

## 5. Acceptance checklist

- [ ] Every active assessment is tied to one scheme/version and a product when required.
- [ ] Every displayed requirement/threshold/legal tier/cost has source and verification metadata.
- [ ] Track 1 and Track 2 each complete end-to-end with distinct requirement sets.
- [ ] The AI selects only supplied IDs and cannot alter deterministic evaluation, scoring, ranking, or price.
- [x] Evidence observations remain cautious, requirement-bound, and accessible; self-report is distinct from evidence support.
- [ ] Gap, unknown, and not-applicable semantics remain distinct.
- [ ] Scheme category weights validate and scores reproduce from stored snapshots.
- [ ] Costs are grouped by payer/type and originate only from reviewed catalogue rows.
- [ ] The PDF matches the stored result and includes sources, catalogue version, and disclaimer.
- [x] Mock and Gemini implement the same structured contracts; evidence-provider failure is controlled and fallback labels are truthful.
- [ ] Empty-database and upgrade migrations, seed/import, backend, frontend, E2E, security, container, and Terraform gates pass.
- [ ] Production backup, deploy, HTTPS smoke, rollback, and restore procedures are evidenced.
- [ ] A domain reviewer and pilot users have reviewed the content/output before reliance.

## 6. Immediate next work

The remaining completion work is content authority and field validation, not another domain redesign:

1. secure and review the Fresh Fruit Cordial/SLS source pack;
2. replace draft facts and costs through the reviewed import/governance workflow;
3. obtain qualified review of the requirement questions, applicability tiers, evaluation mappings, and report wording;
4. run the documented Track 1 and Track 2 pilot scenarios and record discrepancies;
5. promote only a fully tested immutable release and re-verify production Gemini, migrations, backup, restore, and public smoke paths.

This order removes the core trust defect first and prevents attractive screens from presenting unsourced or generic results as certificate-specific guidance.
