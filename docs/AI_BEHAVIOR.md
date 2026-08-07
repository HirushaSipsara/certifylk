# AI behavior contract

## Responsibilities

AI may: select relevant IDs from supplied approved questions; convert informal production-step text into typed stages/tags; return cautious evidence observations and confidence; identify unresolved clarification IDs from supplied candidates; and explain already-calculated roadmap items in plain language.

AI may not define or interpret official certification rules, make legal decisions, inspect a facility, claim compliance, assign requirement status directly without deterministic rules, calculate scores or priorities, invent recommendations/prices, request an unapproved evidence type, or act on document/image instructions.

## Provider interface

```python
class AIProvider(Protocol):
    async def plan_adaptive_questions(...): ...
    async def extract_process(...): ...
    async def analyze_evidence(...): ...
    async def plan_clarifications(...): ...
    async def explain_roadmap(...): ...
```

Every operation accepts a structured application payload and returns a Pydantic v2 model. Core response shapes are:

- Question plan: `question_ids: list[str]`, `reason: str`.
- Process extraction: ordered `stages` with source step, normalized name, supplied approved tags, and confidence; plus uncertainties. The approved process-tag whitelist is included in both the application payload and structured-output schema.
- Evidence analysis: `observations` with evidence request ID, requirement ID, observation text, polarity (`supports`, `concern`, `unclear`), and confidence 0–1.
- Clarification plan: `question_ids` and reason.
- Roadmap explanations: recommendation ID and simple explanation. Cost/gain inputs are repeated as immutable context, never model outputs.

The Gemini adapter is implemented inside the FastAPI monolith. It uses one-shot
`generateContent` calls with JSON Schema output, low-temperature generation, bounded
output tokens, backend-only credentials, and inline image/PDF evidence. It does not
expose a separate AI HTTP service or change the frontend/API workflow.

## Whitelist enforcement

The backend supplies candidate question IDs and allowed evidence/requirement identifiers in every relevant call. It rejects an output containing an unknown ID before persistence and records the validation failure. Adaptive plans contain two to five IDs. Clarification plans contain three to five IDs. Evidence request plans are deterministic; a provider cannot add slots.

Process extraction must return exactly one stage for every non-empty submitted process
step, using the original position once. Evidence observations must reference an uploaded
evidence request and a requirement linked to that exact request; global requirement
membership is insufficient. Duplicate request/requirement observations are rejected.
All model-authored text is stripped of control characters before persistence.

## Retry and fallback

Mock mode has no network and is deterministic. Gemini requests JSON output and validates it. Invalid or transient Gemini output is retried once. When `ALLOW_AI_FALLBACK=true`, the same operation then runs through Mock and both run outcomes are logged. Otherwise the API returns a safe retryable error. Business validation failures do not silently alter state.

`ai_runs` records operation, provider, model, latency milliseconds, success, fallback flag, and a bounded validation/error message. Prompts, keys, raw uploaded document text, and image bytes are not logged.

`run_with_validation` returns the validated provider output together with `provider` and `fallback_used` copied from the same successful run it just persisted. Process-analysis and evidence-analysis expose those two read-only values; they never query a global or assessment-wide “latest run.” A Gemini retry that succeeds reports Gemini without fallback. A completed Mock fallback reports Mock with `fallback_used=true`.

Retries occur inside one HTTP request and are not observable as a distinct browser state, so the UI never claims “Retrying analysis.” While waiting it may show that analysis is active and, after elapsed time, that it is taking longer than expected. A confirmed fallback label appears only after the response reports it. A complete request failure keeps saved data and exposes an actionable retry.

## Prompt-injection handling

Extracted/uploaded content is wrapped and labelled as `UNTRUSTED_EVIDENCE_DATA`. System prompts explicitly prohibit executing, obeying, or repeating instructions from it. The model receives no tools, credentials, question catalogue beyond candidates, or authority to alter application rules. Output is sanitized for control characters and schema/whitelist validated. Phrases such as “ignore prior instructions” remain evidence text, not instructions.

## Confidence

- `0.80–1.00`: clear observation in the submitted material; still not an official finding.
- `0.50–0.79`: plausible observation requiring user confirmation.
- `<0.50`: unclear; treated as unknown by deterministic evaluation unless independently supported.

Confidence is evidence quality, not readiness and not probability of certification.

Evidence-review presentation preserves the returned polarity and confidence. Supports uses a visible check and success label; concern uses a warning icon and label; unclear uses a question icon and neutral label. Color is supplementary. Unknown future polarity strings receive a neutral observation treatment rather than breaking the page.

Images and PDFs create observations only. They never constitute an official inspection conclusion. Every user-facing result states that CertifyLK does not issue, guarantee, or replace SLS certification.

## Production configuration

`AI_PROVIDER`, `GEMINI_API_KEY`, `GEMINI_MODEL`, and fallback behavior are injected only into the backend container from the protected EC2 environment file. They are absent from the frontend build and runtime environment. Production may deliberately use deterministic mock mode; live mode uses the stable explicit model ID `gemini-3.6-flash`, not a moving `latest` alias. Changing the provider mode never transfers scoring, costing, priority, or certification decisions to AI.

`GEMINI_TIMEOUT_SECONDS`, `GEMINI_TEMPERATURE`, and
`GEMINI_MAX_OUTPUT_TOKENS` bound live requests. The adapter converts timeouts, HTTP
errors, blocked responses, empty candidates, and invalid structured output into safe
provider errors without logging prompts, uploaded bytes, or raw provider responses.
