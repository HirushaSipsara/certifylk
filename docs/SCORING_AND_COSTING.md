# Scoring and costing

## Category and requirement weights

Category weights total 100:

| Category | Weight | Seeded requirements (internal weights) |
|---|---:|---|
| Hygiene and sanitation | 20 | handwashing 6, cleaning 6, chemical separation 4, pest observation 4 |
| Production process control | 20 | defined stages 5, measured cooking control 7, thermometer availability 4, contamination separation 4 |
| Documentation and records | 15 | batch record 6, cleaning record 5, production frequency 4 |
| Raw-material and supplier control | 15 | approved/suitable suppliers 6, supplier register 5, incoming checks 4 |
| Packaging and labelling | 15 | label information 7, food-grade evidence 5, protected filling 3 |
| Storage and traceability | 15 | raised/dry storage 4, finished-product storage 3, batch code 5, distribution trace 3 |

Each requirement weight is expressed as global score points and category members sum exactly to the category weight. A startup assertion and tests enforce both totals.

## Requirement scoring

Statuses and multipliers are `confirmed=1.0`, `partial=0.5`, `gap=0.0`, `unknown=0.0`, and `not_applicable` excluded. Every decision includes evidence references and a deterministic rationale.

A **gap** means submitted evidence affirmatively indicates a missing/inadequate practice. **Unknown** means the system lacks sufficient reliable evidence. Both add zero readiness points, but only gaps may be worded as known deficiencies. Unknowns remain a separate result group and generally recommend verification or record collection.

For category `c`, let applicable seeded category weight be `D_c`, earned points be `E_c = sum(weight × multiplier)`, and fixed published category weight be `W_c`:

`normalized category points = (E_c / D_c) × W_c`

If no requirements apply, the category is marked not applicable and excluded from the overall denominator. Overall raw score is `sum(normalized category points) / sum(applicable category weights) × 100`. Raw Decimal values are stored to four places; rounding occurs only for displayed integers using half-up rounding.

Evidence completeness is separate: `100 × count(applicable requirements with confirmed or partial evidence) / count(applicable requirements)`. It is not confidence in certification.

## Priority and recommendation mapping

Gaps and unknowns map only to active seeded recommendations whose related requirement IDs overlap. Duplicate recommendations are collapsed. Ranking uses a stable tuple:

1. Tier 1: safety-critical confirmed gaps.
2. Tier 2: other high-weight uncovered requirements (weight at least 5).
3. Tier 3: low-cost/high-gain actions (one-time maximum at most LKR 5,000 and gain at least 2 points).
4. Tier 4: remaining documentation actions.
5. Tier 5: capital expenditure.

Within a tier: larger uncovered weight, larger `priority_base`, lower maximum one-time cost, then stable recommendation ID. This makes ranking repeatable.

## Costs

Every cost is loaded from the active `cost_items` row for the recommendation. Min/max values are non-negative integer LKR and min cannot exceed max. The API snapshots one-time and recurring ranges, cost note, currency, and last review date. A missing catalogue cost is a configuration error; AI/free text is never parsed as a price.

Cost summary is the sum of displayed item minima and maxima separately. It is an indicative preparation estimate, excludes official fees/labor unless the catalogue note says otherwise, and must show its review date.

## Expected improvement

A roadmap action's maximum expected gain is the uncovered fraction of its related requirements: `weight × (1 - current multiplier)`. Requirements shared by several actions are assigned to the first ranked action that can address them, preventing double counting. Unknowns use the same theoretical gain but explanations say confirmation is needed. Projected raw score accumulates gains in roadmap order and is capped at 100; displayed projections use half-up rounding.

## Worked chilli-paste example

The seeded sample earns 11/20 hygiene, 7/20 process, 7.5/15 documentation, 3/15 supplier, 3.5/15 packaging, and 0/15 storage/traceability. Its raw readiness score is 32.0000 and displayed score is 32. Ten of 21 applicable requirements have confirmed or partial evidence, so evidence completeness is 48%. The result contains two confirmed strengths, ten partial/confirmed gaps, and nine unknowns.

Cooking measurement and thermometer requirements are currently uncovered, so the first ranked catalogue action is `REC_THERMOMETER`, with an 11-point non-duplicated theoretical gain and a projected score of 43. `REC_TEMP_LOG` then covers the remaining three uncovered batch-record points and projects 46. These projections explain the deterministic roadmap but do not claim that buying equipment or creating a record guarantees certification.
