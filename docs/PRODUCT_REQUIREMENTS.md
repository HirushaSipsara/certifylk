# Product requirements

## Problem and target user

Small Sri Lankan food manufacturers often begin certification preparation with limited time, cash, formal records, and access to specialist guidance. SLS-related requirements can feel technical, evidence may be scattered across paper records and phone photos, and owners may not know which improvements to prioritize. CertifyLK targets the owner or operator of a home-based or small food-production business in Sri Lanka.

Common pain points are uncertainty about what information matters, unfamiliar terminology, incomplete process and supplier records, limited confidence in labels or storage controls, and no simple view of the cost-versus-readiness benefit of the next action.

## Solution and impact

CertifyLK asks plain questions, structures five production steps, requests only relevant evidence, and produces an explainable readiness score and action roadmap. The primary Sustainable Development Goal is **SDG 8: Decent Work and Economic Growth**, supported by helping small businesses build repeatable practices and clearer paths toward market readiness.

AI is necessary for tasks that are variable in wording or media: classifying a user-described product, selecting relevant questions, turning informal process descriptions into stages, extracting cautious observations from photos/PDFs, and explaining a structured roadmap in plain language. AI is not used where reproducibility matters: requirements, scores, priorities, gains, and prices are deterministic.

## Four-page journey

1. **Product profile** — the guest creates an assessment and supplies product, location, scale, workforce, packaging, storage, shelf life, existing certification, record frequency, and optional context. The system validates and saves it, then selects two to five approved process questions.
2. **Manufacturing process** — the user enters exactly five ordered slots, at least three non-empty, and answers the adaptive questions. AI extracts structured stages; deterministic rules and approved types create an evidence plan.
3. **Evidence** — the user uploads up to five requested JPEG/PNG/WebP photos and up to two requested PDFs, or marks each request unavailable. AI returns structured observations with confidence. The system selects three to five approved clarification questions.
4. **Clarification** — the user answers the remaining MCQs. The deterministic engine evaluates requirements, scores readiness and evidence completeness, maps gaps/unknowns to catalogue recommendations, calculates LKR costs and projected gains, and asks AI only for simple explanations.

The landing page exposes one primary `Start Assessment` action plus a sample option. Refresh recovery uses the assessment UUID in both URL and local storage.

## Result structure

- Overall readiness score from 0–100 and separate evidence completeness.
- Six category scores.
- Confirmed strengths, possible gaps, and unknown evidence as distinct groups.
- Ordered action checklist with catalogue-derived one-time/recurring LKR ranges.
- Expected gain and cumulative projected readiness per action.
- Plain-language rationale and evidence references for every status decision.
- Persistent notice that the output is not official SLS approval.

No pass probability is shown.

## Phase 1 success criteria

- A new guest can complete the profile-to-result workflow on desktop or mobile without an account.
- The one-click chilli-paste scenario reaches a complete, reproducible result in mock mode.
- 100% of questions and evidence request types returned by AI pass a server-side whitelist.
- 100% of displayed costs originate from the seeded catalogue.
- Automated tests cover scoring normalization, AI validation, file rules, ranking, the API flow, key UI behavior, and the local happy path.
- Loading, retry/fallback, validation, and unsupported/oversized upload paths are visible and safe.
- AI keys exist only in backend environment configuration.

## Limitations and disclaimer

Phase 1 supports only Sri Lankan food manufacturing and SLS-related preparation readiness. It does not model every product-specific SLS standard, conduct laboratory testing or physical inspection, submit applications, or provide legal advice. Results depend on self-reported and uploaded evidence and may contain unknowns. CertifyLK does not issue, guarantee, or replace SLS certification or decisions by the Sri Lanka Standards Institution.
