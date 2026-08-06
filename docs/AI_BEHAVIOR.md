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

## Whitelist enforcement

The backend supplies candidate question IDs and allowed evidence/requirement identifiers in every relevant call. It rejects an output containing an unknown ID before persistence and records the validation failure. Adaptive plans contain two to five IDs. Clarification plans contain three to five IDs. Evidence request plans are deterministic; a provider cannot add slots.

## Retry and fallback

Mock mode has no network and is deterministic. Gemini requests JSON output and validates it. Invalid or transient Gemini output is retried once. When `ALLOW_AI_FALLBACK=true`, the same operation then runs through Mock and both run outcomes are logged. Otherwise the API returns a safe retryable error. Business validation failures do not silently alter state.

`ai_runs` records operation, provider, model, latency milliseconds, success, fallback flag, and a bounded validation/error message. Prompts, keys, raw uploaded document text, and image bytes are not logged.

## Prompt-injection handling

Extracted/uploaded content is wrapped and labelled as `UNTRUSTED_EVIDENCE_DATA`. System prompts explicitly prohibit executing, obeying, or repeating instructions from it. The model receives no tools, credentials, question catalogue beyond candidates, or authority to alter application rules. Output is sanitized for control characters and schema/whitelist validated. Phrases such as “ignore prior instructions” remain evidence text, not instructions.

## Confidence

- `0.80–1.00`: clear observation in the submitted material; still not an official finding.
- `0.50–0.79`: plausible observation requiring user confirmation.
- `<0.50`: unclear; treated as unknown by deterministic evaluation unless independently supported.

Confidence is evidence quality, not readiness and not probability of certification.

Images and PDFs create observations only. They never constitute an official inspection conclusion. Every user-facing result states that CertifyLK does not issue, guarantee, or replace SLS certification.

## Production configuration

`AI_PROVIDER`, `GEMINI_API_KEY`, `GEMINI_MODEL`, and fallback behavior are injected only into the backend container from the protected EC2 environment file. They are absent from the frontend build and runtime environment. Production may deliberately use deterministic mock mode; live mode uses the stable explicit model ID `gemini-3.6-flash`, not a moving `latest` alias. Changing the provider mode never transfers scoring, costing, priority, or certification decisions to AI.
