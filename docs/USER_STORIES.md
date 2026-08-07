# User stories and acceptance criteria

## Epic A — Choose a certification track

### A1 Product-quality entry

As a Sri Lankan food manufacturer, I want to choose my product category and product so that guidance is based on a relevant product standard.

**Given** the Product Quality entry, **when** I load categories and products, **then** enabled values come from the API and Food Products / Fresh Fruit Cordial is the pilot selection.

### A2 Process/system entry

As a manufacturer, I want to describe my business before seeing GMP, HACCP, and ISO 22000 guidance so the system can recommend a realistic maturity path.

**Given** the Track 2 home action, **when** I start, **then** a guest assessment is created and the business-profile page opens without a product-selection page.

### A3 Guest recovery

As a guest, I want my assessment UUID preserved so a refresh does not destroy progress.

**Given** a created assessment, **when** I refresh or return with its URL, **then** the API state is restored; the UI explains that possession of the URL grants access.

## Epic B — Business screening profile

### B1 Simple business questions

As an owner, I want to provide business name/type, years, scale, markets, current certifications, food-licence status, volume, and a short description without certification jargon.

**Given** a valid profile, **when** I submit it, **then** it is persisted and linked to the assessment and selected product where applicable.

### B2 Validation

As a user, I want useful field errors so I can correct incomplete information.

**Given** missing or invalid required fields, **when** I submit, **then** the UI shows the API/Zod validation near the relevant field and does not duplicate the request.

## Epic C — AI applicability decision

### C1 Ranked pathways

As an owner, I want CertifyLK to rank relevant pathways so I do not have to interpret the certification decision tree alone.

**Given** a saved profile and a DB-supplied scheme candidate list, **when** applicability runs, **then** AI returns only supplied scheme IDs grouped as mandatory, market-required, recommended, or optional and promotes one recommended path.

### C2 Explainable grounding

As a user, I want to see why a scheme is recommended and which supplied source fact supports it.

**Given** an applicability decision, **when** I expand “Why this?”, **then** I see the reasoning, confidence, issuer, source reference, and verification warning without fabricated clauses or legal claims.

### C3 Provider/fallback truth

As a user, I want completed AI work labelled accurately.

**Given** exact-run metadata, **when** the response completes, **then** the UI shows Gemini or confirmed fallback truthfully and shows Mock only in development/test/QA mode; missing metadata remains safe.

## Epic D — Certificate Assessment Hub

### D1 One assessment, one scheme

As a user, I want each attempt attached to a single certification scheme so its requirements and result cannot be mixed with another scheme.

**Given** a chosen/recommended scheme, **when** I open the Hub, **then** it shows the product when applicable, issuer, scheme/version, verification state, and the stages remaining.

### D2 Requirement overview

As a user, I want to review requirement categories, clauses, and sources before supplying evidence.

**Given** an assessment with a scheme, **when** I open Requirements, **then** only active requirements for that frozen scheme version appear with weight, clause/source, and verification status.

## Epic E — Process and evidence

### E1 Process capture

As an owner, I want to describe my production process in simple steps so it can be mapped to relevant controls.

**Given** at least the minimum valid steps, **when** extraction completes, **then** every non-empty input is mapped once to approved tags and provider/fallback metadata is shown.

### E2 Relevant requests

As an owner, I want only evidence relevant to the selected scheme requirements.

**Given** the frozen requirement set, **when** the plan is built, **then** every requested photo/document/lab report/licence references allowed evidence expectations and scheme requirement IDs.

### E3 Safe upload or unavailable

As an owner, I want to upload supported evidence or say I do not have it.

**Given** a requested slot, **when** I upload JPEG/PNG/WebP/PDF within limits or mark unavailable, **then** generated safe storage is used and invalid, oversized, mismatched, or cross-assessment files are rejected.

### E4 Accessible observations

As a user, I want observations distinguished as supports, concern, or unclear with confidence.

**Given** analyzed evidence, **when** review appears, **then** polarity has icon plus text, confidence uses Clear/Plausible/Unclear bands without changing the value, and unknown polarity renders neutrally.

## Epic F — Adaptive clarification

### F1 Ask only unresolved questions

As an owner, I want a small set of targeted questions so I do not repeat information already supported by evidence.

**Given** evaluated profile/process/evidence facts, **when** clarification planning runs, **then** it selects only approved candidates associated with unresolved selected-scheme requirements.

### F2 Whitelist enforcement

As the system, I want unknown question/evidence/requirement IDs rejected so model output cannot change the catalogue.

**Given** AI output containing an unsupplied ID, **when** validation runs, **then** persistence is stopped, the failed run is safely logged, and fallback/error rules apply.

## Epic G — Deterministic result

### G1 Requirement status

As an owner, I want confirmed, partial, gap, unknown, and not-applicable statuses separated so missing evidence is not accused as a known failure.

**Given** submitted facts and evidence, **when** completion runs, **then** deterministic evaluation records a rationale and evidence/source references for each applicable scheme requirement.

### G2 Readiness and completeness

As an owner, I want readiness separate from evidence completeness.

**Given** requirement evaluations, **when** scoring runs, **then** scheme category weights normalize safely, raw/display scores are stored, and completeness counts confirmed/partial evidence separately.

### G3 Roadmap and costs

As an owner, I want prioritized actions and trustworthy LKR estimates.

**Given** gaps/unknowns, **when** the roadmap is built, **then** deterministic ranking uses only scheme-linked catalogue items, costs show payer/type/source/review date, gains do not double count, and AI only explains fixed items.

### G4 Report

As an owner, I want a downloadable report I can discuss with an adviser.

**Given** a stored completed result, **when** I export PDF, **then** it reproduces the result, sources, catalogue version, verification warnings, generation time, and certification disclaimer.

## Epic H — Education and recovery

### H1 My Assessments

As a returning guest, I want to see assessment links remembered in this browser.

**Given** locally remembered UUIDs, **when** I open My Assessments, **then** existing accessible assessments are listed and stale/missing IDs can be removed without implying account security.

### H2 Understand Certification

As a new manufacturer, I want a plain-language guide to product versus management-system certification and mandatory versus market-required pathways.

**Given** reviewed educational content, **when** I open the page, **then** it cites authoritative sources and repeats that final applicability must be confirmed with the relevant body.

## Epic I — Reliability, security, and demo

### I1 Loading, long-running, and retry

As a user, I want truthful progress and an actionable retry after complete failure.

**Given** an AI request, **when** it runs, **then** the UI may show analyzing and taking longer; it never claims an unobservable retry, and retry is offered only after request failure.

### I2 Source and content governance

As the system owner, I want standards and costs versioned and reviewed so old assessments remain reproducible.

**Given** a catalogue update, **when** it is imported, **then** source/reviewer/effective-date metadata is required and previous completed snapshots remain unchanged.

### I3 Deterministic samples

As a judge, I want completed examples demonstrating the same real workflow.

**Given** Mock mode, **when** I load the Fresh Fruit Cordial/SLS example or execute Track 2 test scenarios, **then** the paths are reproducible and show at least two strengths, a gap, an unknown, a source-linked cost, AI metadata, and the disclaimer.

### I4 Release safety

As an operator, I want failed tests to block production and data preserved through deployment.

**Given** a release commit, **when** CI/deployment runs, **then** all checks pass for the exact SHA, migrations run explicitly after backup, volumes remain intact, health gates pass, and rollback never silently downgrades the database.
