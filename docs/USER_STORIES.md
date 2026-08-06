# User stories and acceptance criteria

## Epic A — Start and resume assessment

### A1 Start without an account

As a food business owner, I want to start an assessment without creating an account so that I can begin quickly.

**Given** the landing page, **when** I select Start Assessment, **then** a guest assessment is created and Page 1 opens without authentication.

### A2 Unique assessment identity

As a food business owner, I want a unique assessment link or ID so that the application can load my current progress during the local session.

**Given** an assessment was created, **when** its route is shown, **then** the URL contains its UUID and loading that URL retrieves the same assessment.

### A3 Preserve progress

As the system, I want to preserve the current page and answers so that browser refreshes do not destroy progress.

**Given** saved answers, **when** the browser refreshes, **then** the API state is restored and the UUID remains in local storage.

## Epic B — Product and business profile

### B1 Plain profile questions

As a food business owner, I want to answer simple MCQs about my product, production location, scale, packaging, storage, shelf life, certifications, and records so that I do not need certification expertise.

**Given** Page 1, **when** I view the form, **then** each required topic uses plain, labelled controls.

### B2 Other values

As a food business owner, I want an Other option with free text so that unusual products and practices can be represented.

**Given** a supported field, **when** I choose Other, **then** a required free-text control appears and is persisted.

### B3 Validation

As the system, I want to validate required fields and display useful errors.

**Given** missing or invalid data, **when** the profile is submitted, **then** submission is blocked or a field-specific API error is displayed.

### B4 Product classification

As the AI assessment engine, I want to classify the product and identify missing information.

**Given** a valid profile, **when** planning runs, **then** structured tags and missing-information flags conform to the AI schema.

### B5 Approved adaptive questions

As the AI assessment engine, I want to select only relevant next questions from an approved question bank.

**Given** a candidate whitelist, **when** AI returns a plan, **then** only two to five supplied IDs are accepted; unknown IDs fail validation.

## Epic C — Manufacturing process

### C1 Five process spaces

As a food business owner, I want five short spaces to enter my main production steps.

**Given** Page 2, **when** it renders, **then** exactly five ordered, labelled inputs are shown and at least three must be non-empty.

### C2 Adaptive MCQs

As a food business owner, I want to answer a small number of adaptive MCQs selected from my profile.

**Given** profile planning completed, **when** Page 2 loads, **then** two to five persisted approved questions are displayed.

### C3 Structured process

As the AI assessment engine, I want to convert the five free-text steps into structured manufacturing stages.

**Given** valid process steps, **when** analysis runs, **then** ordered stages with approved tags and confidence values are stored.

### C4 Process uncertainty

As the AI assessment engine, I want to identify process-related uncertainty without inventing certification rules.

**Given** ambiguous steps, **when** analysis runs, **then** uncertainties are observations tied to known requirements and never described as official violations.

## Epic D — Evidence collection

### D1 Relevant photos

As a food business owner, I want the system to request only relevant photos.

**Given** the process tags, **when** the evidence plan is built, **then** it contains only whitelisted relevant photo types.

### D2 Five-photo maximum

As a food business owner, I want to upload up to five photos.

**Given** Page 3, **when** uploads are requested, **then** no more than five photo slots exist.

### D3 One or two documents

As a food business owner, I want to upload one or two requested documents.

**Given** the evidence plan, **when** Page 3 renders, **then** at most two whitelisted PDF document requests appear.

### D4 Evidence observations

As the AI assessment engine, I want to inspect images and PDFs and return structured observations with confidence values.

**Given** supported stored files, **when** analysis runs, **then** validated observations reference requests/requirements and include confidence from 0 to 1.

**Given** evidence observations are returned, **when** the review state renders, **then** supports, concern, and unclear use visible text plus distinct icons, and confidence is labelled Clear, Plausible, or Unclear using the documented bands.

### D5 Safe file rejection

As the system, I want to reject unsupported or oversized files safely.

**Given** an invalid MIME type or size, **when** upload is attempted, **then** the API returns 415 or 413 without persisting the file.

### D6 Unavailable evidence

As the system, I want to mark a requested item as unavailable when the user cannot provide it.

**Given** an open request, **when** the user selects I do not have this, **then** the request is persisted as unavailable.

## Epic E — Final clarification

### E1 Resolve high-priority unknowns

As the AI assessment engine, I want to identify unresolved high-priority information after reviewing answers and evidence.

**Given** completed evidence handling, **when** clarification planning runs, **then** high-priority applicable candidates are preferred.

### E2 Three to five questions

As a food business owner, I want to answer only three to five final MCQs.

**Given** Page 4, **when** it renders, **then** three to five questions are shown with Other only where allowed.

### E3 Approved clarification bank

As the system, I want all clarification questions to come from the approved question bank.

**Given** the model output, **when** it contains an unknown ID, **then** validation rejects it and safe fallback rules apply.

## Epic F — Readiness result

### F1 Overall score

As a food business owner, I want to see an overall readiness score.

**Given** a completed assessment, **when** the result loads, **then** a deterministic integer score from 0 to 100 is displayed.

### F2 Category scores

As a food business owner, I want category-level scores.

**Given** a result, **when** categories render, **then** all six applicable category scores are shown.

### F3 Separate evidence states

As a food business owner, I want confirmed strengths, possible gaps, and unknown evidence shown separately.

**Given** evaluated requirements, **when** evidence summary renders, **then** confirmed, gap/partial, and unknown groups remain distinct.

### F4 Prioritized actions

As a food business owner, I want a prioritized checklist of next actions.

**Given** uncovered requirements, **when** the roadmap is built, **then** deterministic safety, weight, value, documentation, and capital rules order it.

### F5 Cost ranges

As a food business owner, I want an estimated cost range for each action.

**Given** a recommendation, **when** rendered, **then** its one-time and recurring LKR ranges come from seeded costs.

### F6 Expected gain

As a food business owner, I want the expected readiness improvement for each action.

**Given** related uncovered requirement weights, **when** an item is calculated, **then** its non-duplicated deterministic gain is shown.

### F7 Cumulative projection

As a food business owner, I want to see the projected score after each completed item.

**Given** the ordered roadmap, **when** items render, **then** each shows the capped cumulative score after preceding gains.

### F8 Rationale

As a food business owner, I want an explanation of why each action was recommended.

**Given** a structured roadmap item, **when** explanation succeeds or falls back, **then** a simple non-certifying rationale is displayed.

### F9 Disclaimer

As a food business owner, I want a clear statement that the result is not official SLS approval.

**Given** a result, **when** it renders, **then** the certification disclaimer is prominent.

### F10 Deterministic model

As the system, I want scoring and costing to remain deterministic and explainable.

**Given** identical persisted inputs and catalogue versions, **when** results are regenerated, **then** scores, costs, gains, and order are identical.

## Epic G — Reliability and safety

### G1 Loading feedback

As a user, I want loading indicators during AI analysis.

**Given** an analysis request is pending, **when** the UI waits, **then** a labelled blocking loading overlay prevents duplicate submission.

**Given** an analysis remains pending beyond the normal threshold, **when** the threshold is reached, **then** the UI says it is taking longer than expected without claiming a retry occurred.

### G2 Retry

As a user, I want a retry option when AI processing fails.

**Given** a retryable API error, **when** it is displayed, **then** the user can submit that operation again without losing saved data.

Internal Gemini retries are not separately visible to the browser and are never simulated in the UI.

### G3 Deterministic fallback

As the system, I want a deterministic fallback when the AI provider is unavailable.

**Given** Gemini fails and fallback is enabled, **when** the single retry is exhausted, **then** Mock AI completes the operation and the run is logged.

**Given** fallback completed an analysis, **when** its response is shown, **then** the UI displays “Completed using fallback analysis” only because `fallback_used=true` was returned for that exact request.

### G7 AI execution transparency

As a user, I want to know which analysis provider completed the current operation so that AI behavior is transparent.

**Given** a process or evidence analysis response, **when** its review state renders, **then** Gemini is named only when `provider=gemini`, fallback is named only when confirmed, Mock is named only in development/test or enabled QA display mode, and missing metadata is handled safely.

### G4 Pydantic validation

As the system, I want AI outputs validated against Pydantic schemas.

**Given** any provider response, **when** it reaches the application, **then** schema and whitelist validation occurs before persistence.

### G5 Backend-only secrets

As the system, I want AI API keys kept only in backend environment variables.

**Given** the frontend bundle, **when** configuration is inspected, **then** it contains only the public API base URL and no AI secret.

### G6 Demonstration sample

As a judge, I want a sample chilli-paste assessment that demonstrates the complete workflow.

**Given** the landing page, **when** Load Sample Assessment is selected, **then** a completed realistic sample opens with strengths, gaps, unknowns, costs, gains, and disclaimer.
