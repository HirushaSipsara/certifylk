# CertifyLK Pilot Feedback & Discrepancy Register

**Document Version:** 1.0.0 (Phase I Template)  
**Governance Scope:** Fresh Fruit Cordial (`SLS_MARK_CORDIAL` / `SLS 187`) & Process Schemes (`SLS_GMP`, `SLS_HACCP`, `ISO_22000`)  
**Status:** ACTIVE TEMPLATE — REAL ENTRIES TO BE POPULATED DURING PILOT SESSIONS

---

## 1. Discrepancy Classification Taxonomy

To ensure objective and actionable feedback, findings from domain reviewers and pilot participants are categorized into standard discrepancy classes:

| Discrepancy Type | Definition |
|---|---|
| **overstated_readiness** | CertifyLK assessed preparation as more advanced or complete than actual factory readiness warrants. |
| **understated_readiness** | CertifyLK flagged compliant factory practices or valid records as an unmet preparation gap. |
| **incorrect_requirement_mapping** | The tool mapped factory process steps or evidence to an irrelevant standard clause or requirement ID. |
| **incorrect_evidence_interpretation** | AI or rule-based observation assigned inaccurate polarity (`supports`, `concern`, `unclear`) to uploaded material. |
| **unresolved_ambiguity** | Clarification questions failed to resolve ambiguous evidence or created confusion. |
| **incorrect_applicability** | The tool recommended an inappropriate certification pathway for the business scale/market context. |
| **cost_source_discrepancy** | Displayed cost figure, recurrence period, or quote-required status conflicts with actual published fee schedules. |
| **unclear_wording** | Phrasing in requirements, questions, or roadmap actions caused user misunderstanding. |
| **missing_guidance** | A vital statutory or food safety requirement was absent from the catalogue. |
| **accepted_output** | Reviewer confirmed CertifyLK output accurately reflects standard requirements and factory preparation state. |

---

## 2. Discrepancy Severity Model

- **CRITICAL:** Material defect that could cause unsafe food practices, misstate statutory legal duties, invent non-existent standard clauses, or mislead manufacturers regarding official regulatory status. *Any unresolved critical discrepancy blocks production expansion.*
- **HIGH:** Significant error that alters the readiness score or prioritizes ineffective capex/opex roadmap investments.
- **MEDIUM:** Non-critical inaccuracy in explanatory text, wording, or minor cost notes where core guidance remains broadly safe.
- **LOW:** Cosmetic text, typography, layout, or minor clarification phrasing improvements.

---

## 3. Discrepancy Register

> [!NOTE]
> Entries in this table are **EXAMPLE / TEMPLATE ONLY** for illustrating the recordkeeping schema. Real manufacturer session data will be entered upon pilot execution.

| Pilot ID | Assessment ID | Track / Scheme | Requirement / Source ID | Discrepancy Type | Severity | CertifyLK Output | Reviewer Expected Output | Recommended Action | Resolution Status |
|---|---|---|---|---|---|---|---|---|---|
| *PILOT-MFG-001* | *`sample-demo-01`* | *Track 1 / SLS_MARK_CORDIAL* | *`CORDIAL_PAST_01`* | *accepted_output* | *N/A* | *Identified batch pasteurization log gap* | *Agrees: continuous temp log required by SLS 187* | *Retain current rule* | *VERIFIED* |
| *PILOT-MFG-002* | *`sample-demo-02`* | *Track 1 / SLS_MARK_CORDIAL* | *`CORDIAL_WATER_01`* | *unclear_wording* | *LOW* | *"Provide potable water microbial test"* | *"Specify SLS 614 standard for potable water"* | *Update catalogue source note in next revision* | *LOGGED FOR REV 2* |
| *[TEMPLATE ONLY]* | *`UUID`* | *Track / Scheme* | *Req ID* | *Classification* | *CRITICAL / HIGH / MED / LOW* | *Observed tool output* | *Expert standard interpretation* | *Proposed correction* | *OPEN / RESOLVED* |

---

## 4. Discrepancy Action & Retest Protocol

When a **HIGH** or **CRITICAL** discrepancy is logged:
1. **Root Cause Analysis:** Determine whether defect is in the catalogue definition, AI grounding boundary, scoring formula, or UI rendering.
2. **Versioned Correction:** Update the versioned catalogue or domain rule via an explicit migration and seed update. AI prompts are **never** tuned to paper over underlying catalogue defects.
3. **Regression Suite:** Execute backend unit tests, costing tests, and API integration tests.
4. **Retest Verification:** Re-evaluate the historical assessment fixture to verify corrected output without regressing other schemes.
