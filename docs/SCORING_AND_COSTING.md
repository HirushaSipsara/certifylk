# Scoring and costing

## Non-negotiable rule

Requirement evaluation, scores, evidence completeness, ranking, costs, gains, and projections are deterministic. AI may explain these outputs but cannot calculate or modify them.

## Current legacy baseline

The existing generic engine uses six categories totaling 100:

| Category | Weight |
|---|---:|
| Hygiene and sanitation | 20 |
| Production process control | 20 |
| Documentation and records | 15 |
| Raw-material and supplier control | 15 |
| Packaging and labelling | 15 |
| Storage and traceability | 15 |

This remains the deterministic chilli-paste regression engine. The sample produces `32.0000` raw / `32` displayed. That number must remain stable while legacy code exists, but it is not a certificate-specific Fresh Fruit Cordial/SLS score.

## Scheme-specific weights

Each `certification_scheme.category_weights` and its active `scheme_requirements.weight` values define that scheme’s 100-point model. Before activation, deterministic validation must prove:

- category weights sum to 100;
- requirements within each category sum to the category’s weight;
- every requirement belongs to the assessment’s frozen scheme version;
- weights are non-negative Decimals and cannot be supplied by AI;
- completed results snapshot scheme, standard version, catalogue revision, scores, costs, and roadmap items.

GMP, HACCP, ISO 22000, and SLS Cordial may have different category structures. The UI must not assume the legacy six categories.

When an assessment has `scheme_id`, `POST /complete` evaluates only that scheme’s active `scheme_requirements`, uses that scheme’s category weights, and creates a JSON `roadmap_snapshot` from `scheme_cost_items`. Legacy assessments without `scheme_id` continue to use the global chilli-paste regression catalogue.

## Requirement scoring

Statuses and multipliers remain:

- `confirmed = 1.0`
- `partial = 0.5`
- `gap = 0.0`
- `unknown = 0.0`
- `not_applicable` excluded from the denominator

A gap requires affirmative evidence of a missing/inadequate practice. Unknown means evidence is insufficient. They score the same but must be displayed and explained separately.

For scheme-specific assessments, controlled `evaluation_rule` mappings may derive a status from an approved profile field, adaptive/clarification answer, ordered process-step completeness, or a validated evidence observation. Answer-derived status therefore contributes to readiness without being represented as uploaded evidence.

For category `c`, with applicable requirement denominator `D_c`, earned points `E_c`, and configured category weight `W_c`:

`category points = (E_c / D_c) × W_c`

Overall readiness is normalized across applicable category weights. Raw Decimal scores are stored; display uses half-up integer rounding. Empty categories are safely excluded.

Evidence completeness is separate:

`100 × applicable requirements with confirmed or partial evidence / all applicable requirements`

Only an accepted evidence observation reference counts in that numerator. Profile answers and process answers may affect readiness but do not increase evidence completeness. It is not readiness, AI confidence, or probability of certification.

## Evidence references

Every status requires deterministic rationale and references to profile answers, process steps, clarification answers, evidence observations, and the scheme requirement/source. A model observation never directly becomes official compliance; the rule engine interprets validated facts according to the reviewed `evaluation_rule`.

## Roadmap priority

The stable ordering remains:

1. safety-critical confirmed gaps;
2. other high-weight uncovered requirements;
3. low-cost/high-gain actions;
4. remaining documentation improvements;
5. capital expenditure.

Within a tier use uncovered weight, configured priority, lower maximum one-time cost, then stable ID. Scheme isolation is mandatory.

## Costs

Scheme-specific results read only active `scheme_cost_items` and separate:

- `certifying_body_fee`;
- `lab_testing_fee`;
- `business_capex`;
- `business_opex`.

Each numeric range needs currency LKR, min/max, recurrence, source note, effective date, and last-reviewed date. If no reliable value exists, display “quote required”/no numeric estimate rather than inventing one. AI and user text are never parsed as prices.

## Expected improvement

An action’s theoretical maximum gain is the uncovered fraction of its related applicable requirement weights: `weight × (1 − current multiplier)`. Shared requirements are assigned to the first ranked action capable of addressing them, preventing double counting. Projections accumulate in order and cap at 100. Wording must state that performing an action still requires evidence and does not guarantee certification.

## Required worked examples

- Preserve the legacy chilli-paste `32.0000 / 32` regression example until legacy retirement.
- Add a reviewed Fresh Fruit Cordial/SLS worked example after certificate-scoped evaluation is complete.
- Add at least one Track 2 domestic case and one export/supermarket case. Each must publish its frozen scheme/version, category math, evidence completeness, costs, and deterministic expected-gain calculation.
