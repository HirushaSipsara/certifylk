# Product requirements

## Problem and target user

Small Sri Lankan food manufacturers often do not know which certification or licence applies to their product and market, what a specific scheme actually requires, which evidence they already possess, or which improvement gives the best practical next step. Generic hygiene quizzes cannot provide defensible guidance because they are not traceable to a particular standard, clause, certification body, or fee source.

The primary user is an owner or operator of a household-scale producer, small workshop, or small factory manufacturing food in Sri Lanka.

## Product outcome

CertifyLK converts a short business/product profile and user-provided evidence into:

1. an AI-assisted, source-grounded list of applicable certification pathways;
2. one recommended path with an explanation and cited catalogue facts;
3. a separate assessment for one product/scheme pair (or one system scheme for Track 2);
4. requirement-level strengths, gaps, and unknowns linked to sources;
5. a deterministic, prioritized roadmap with source-dated LKR estimates.

The primary impact target is **SDG 8: Decent Work and Economic Growth**, helping small manufacturers build repeatable practices and qualify for stronger markets without pretending to replace official certification.

## Why AI is necessary

AI handles ambiguity and unstructured material: it reasons over a supplied catalogue to rank applicable schemes, normalizes informal process descriptions, extracts cautious observations from images/PDFs, selects unresolved questions from a whitelist, and explains deterministic roadmap actions in plain language. AI does not create laws, standards, clauses, thresholds, costs, scores, statuses, or official decisions.

## Target user journey

### Home

- Two primary entries: Product Quality and Process & System.
- Live scheme summaries loaded from the API.
- A clearly labelled completed example, disclaimer, “What we offer,” and education link.

### Track 1 — Product Quality

1. Select category and product. Food Products / Fresh Fruit Cordial is the enabled pilot.
2. Enter business name/type, years, scale, markets, existing certifications, food-licence status, production volume, and a short description.
3. Run bounded AI applicability reasoning over database-supplied schemes/rules. Show mandatory, market-required, recommended, and optional groups and promote one recommended path.

### Track 2 — Process & System

1. Start directly from the home page because GMP/HACCP/ISO 22000 are not product-specific in this pilot.
2. Enter the same business screening profile.
3. Run applicability reasoning for Track 2 and rank SLS GMP, SLS HACCP, and ISO 22000 based on the submitted market and scale.

### Certificate Assessment Hub

Each assessment belongs to one scheme and, for product schemes, one product. The target steps are:

1. **Requirement overview:** show scheme categories, clauses, source links, version/verification status, and what evidence may demonstrate each requirement.
2. **Evidence and process:** collect relevant photos, PDF documents, process answers, or unavailable states, all tagged to the scheme requirements they support.
3. **Clarification:** ask only unresolved, approved questions grounded in the selected requirement set.
4. **Gap analysis:** deterministically evaluate requirements as confirmed, partial, gap, unknown, or not applicable.
5. **Guidance and costs:** show clause-linked actions, certification-body/laboratory/business-cost separation, expected gain, cumulative projection, and downloadable report.

### Shared pages

- “My Assessments” lists locally recoverable guest assessments without implying secure accounts.
- “Understand Certification” explains SLS versus management-system schemes, mandatory versus voluntary/market-required pathways, and the readiness disclaimer.

## Result contract

- Selected product and scheme, issuing body, standard/version, source and verification banner.
- Overall readiness and separate evidence completeness.
- Scheme-specific category and requirement statuses.
- Confirmed strengths, confirmed/possible gaps, and unknown evidence separately.
- Evidence references and clause/source references for every decision.
- Prioritized actions with one-time and recurring LKR ranges, payer/cost type, source note, review date, expected gain, and cumulative projection.
- AI-written narrative only around fixed structured facts.
- No pass probability and no certification promise.

## Success criteria

- Both authorized tracks complete from landing to a persisted, scheme-specific result in Mock mode.
- Gemini can complete the same bounded operations with backend-only credentials and validated outputs.
- Every returned scheme/question/evidence/requirement ID is checked against the exact supplied whitelist.
- Every requirement, legal tier, threshold, and cost displayed to users has versioned source metadata and verification status.
- Unverified content is visibly labelled and cannot be mistaken for official guidance.
- Scoring/costing are repeatable and tests prove cross-scheme isolation.
- Mobile, keyboard, loading, error, fallback, upload, refresh, and deployment smoke paths pass.

## Limitations and disclaimer

The current catalogue is a pilot, not a complete inventory of Sri Lankan certification law or standards. Purchased/copyrighted standards must not be reproduced beyond permitted summaries. Legal applicability and fees can change and require owner review. Uploaded evidence is not a physical audit. CertifyLK provides readiness guidance only and users must confirm final requirements with SLSI, the relevant regulator/certification body, and qualified professionals.
