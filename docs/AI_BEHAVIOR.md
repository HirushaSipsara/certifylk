# AI behavior contract

## Principle

AI makes bounded, explainable judgments over facts supplied by CertifyLK. It is not the source of standards, law, thresholds, prices, scores, or certification decisions. Every identifier in model output is untrusted until validated against the candidate list for that exact request.

## Current operations

`AIProvider` currently supports:

1. `plan_applicable_schemes` — rank supplied certification scheme IDs for a saved business/product context.
2. `plan_adaptive_questions` — select approved process question IDs.
3. `extract_process` — normalize non-empty submitted process steps into approved stages/tags.
4. `analyze_evidence` — return requirement-bound observations with polarity and confidence.
5. `plan_clarifications` — select approved unresolved question IDs.
6. `explain_roadmap` — explain deterministic recommendation items without changing them.

Mock and Gemini implement the same typed contract. Mock is deterministic and is the default for tests/demos.

## Applicability behavior

The backend loads active schemes for the resolved track and supplies each actionable scheme’s ID, name, tier, applicability rule, summary, and body plus the structured business profile/product. A Food Business Registration pathway is deterministically classified as already held when the saved profile says the business currently holds that registration/licence; it is excluded from the AI action candidates and returned separately for acknowledgement. AI returns:

- `decisions`: whitelisted `scheme_id`, tier, confidence, reasoning, and source reference;
- `recommended_path_scheme_id`: null or one supplied ID;
- `overall_reasoning`.

The backend rejects unknown IDs and persists the validated decision plus already-held scheme IDs in assessment profile data. Track 1 candidates are actionable product-quality schemes; Track 2 candidates are process-management schemes. The optional business-profile narrative is included in the bounded AI context. The current implementation supplies that context in one provider operation. It is not yet proof of Gemini function/tool calls. A later read-only tool registry must retain exactly the same whitelist and safety boundary.

Mandatory or market-required wording must come from reviewed catalogue facts. AI may explain ambiguity but may not upgrade an optional/recommended scheme to a legal mandate without a supplied rule.

## Evidence and clarification behavior

- Uploaded files/text are wrapped as untrusted evidence data.
- Evidence files are reopened through `StorageProvider` and analyzed in sequential multimodal batches of at most two files rather than one unbounded or concurrent burst. Gemini receives the actual image/PDF bytes as provider-supported inline data with the stored MIME type, plus the selected scheme requirement title, description, source metadata, verification state, and deterministic evaluation rule retrieved from PostgreSQL.
- Observations reference an uploaded request and a requirement allowed for that exact request.
- Every certificate-specific uploaded request/requirement pair must receive exactly one validated observation; legacy requests that map one file to multiple requirements must receive at least one. Omitted requests and duplicate pairs fail validation and use the configured retry/fallback path.
- Polarity is `supports`, `concern`, or `unclear`; confidence remains the model-returned validated 0–1 value.
- AI does not perform an official pass/fail inspection and must not state a limit from memory.
- The target scheme-specific operation must receive the retrieved requirement/source/threshold data before comparison.
- Each persisted observation records the exact successful batch provider, fallback flag, and validation status. The evidence page shows those values with polarity, confidence band, and observation text before the user continues. Retrying is a real new backend analysis request with replace semantics; it is not simulated by a timer and does not accumulate duplicate observation rows.
- Clarification selects only supplied question IDs linked to unresolved selected-scheme requirements.

## Roadmap behavior

AI receives only already-ranked, already-priced roadmap items and their source references. It may simplify the explanation but may not add/remove/reorder actions, change cost/gain/projection values, create a clause, or promise readiness/certification.

## Deterministic exclusions

AI never controls:

- catalogue content, standard version, source verification, legal tier, or applicability candidate set;
- requirement status rules or multipliers;
- category weights/normalization, readiness, evidence completeness, or rounding;
- recommendation mapping/ranking, cost lookup/sums, expected gain, or projection;
- upload validation, page transition, persistence authorization, or release behavior.

## Validation and whitelist enforcement

- Applicability scheme IDs must be a subset of the supplied active schemes.
- Adaptive plans contain only supplied IDs and enforce their count.
- Process extraction maps every non-empty source position once and uses approved tags.
- Evidence observations require exact request/requirement membership; duplicates are rejected.
- Clarification IDs must come from supplied candidates and enforce their count.
- Roadmap explanations must match the deterministic recommendation IDs exactly.
- All model-authored text is length-bounded and stripped of control characters before persistence.

Unknown IDs or invalid structured output fail validation, are safely logged, and may trigger the configured retry/fallback path. They are never silently repaired into a different domain answer.

## Retry, fallback, and transparency

Gemini structured output is validated and may retry once on a transient/invalid provider response. HTTP 429/5xx responses use a bounded provider-supplied retry delay when available. With `ALLOW_AI_FALLBACK=true`, only the failed evidence batch executes through Mock; already validated Gemini batches remain Gemini observations. `ai_runs` records operation, provider, model, latency, success, fallback flag, and a bounded safe provider/validation error—not prompts, keys, raw evidence, or model responses.

`run_with_validation` returns validated output plus provider/fallback metadata from the exact successful run. The UI may show:

- “Analyzing …” while the request is pending;
- “Analysis is taking longer than expected” after elapsed time;
- “Analyzed by Gemini” only when the response confirms Gemini without fallback;
- “Completed using fallback analysis” only when confirmed;
- “Analyzed by Mock AI” only in development/test or explicit QA display mode;
- an actionable retry only after complete request failure.

Internal retry is not browser-observable, so the UI must not claim “Retrying analysis.” Metadata may be absent after refresh/older responses and must degrade safely.

## Prompt-injection handling

Uploaded/extracted content is labelled `UNTRUSTED_EVIDENCE_DATA`. Instructions embedded in documents or images are data, never commands. Providers receive no credentials, unrestricted tools, or authority to change the catalogue. Phrases such as “ignore previous instructions” are not followed or repeated unnecessarily.

## Confidence and polarity presentation

- `0.80–1.00`: **Clear** observation, still not an official finding.
- `0.50–0.79`: **Plausible**, requires user/independent confirmation.
- `<0.50`: **Unclear**, normally unknown unless independently supported.

`supports` uses check icon plus visible success text; `concern` uses warning icon plus visible warning text; `unclear` uses question icon plus neutral text. Color is not the sole signal. Unknown future polarity renders neutrally. Confidence is evidence quality, not certification probability or readiness.

## Grounding and source display target

Every applicability/evidence/narrative output should expose only references to facts actually supplied for its exact execution. If read-only tools are implemented, log safe tool names and catalogue record IDs—not copyrighted text, prompts, or evidence. Never fabricate a grounding trail. Unverified source rows remain visibly unverified even when Gemini confidence is high.

## Production configuration

`AI_PROVIDER`, `GEMINI_API_KEY`, `GEMINI_MODEL`, timeout/temperature/token limits, and fallback settings exist only in the backend environment. Frontend variables never contain provider secrets. Provider changes do not change deterministic domain behavior.
