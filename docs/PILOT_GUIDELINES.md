# CertifyLK Pilot Guidelines & Domain Review Protocol

**Version:** 1.0.0 (Phase I Protocol)  
**Target Product Scope:** Fresh Fruit Cordial (`PROD_CORDIAL`)  
**Target Scheme:** SLS Mark — Fresh Fruit Cordial (`SLS_MARK_CORDIAL` / `SLS 187`)  
**Secondary Observation Scope:** SLS GMP (`SLS_GMP`), SLS HACCP (`SLS_HACCP`), ISO 22000:2018 (`ISO_22000`)

---

## 1. Mission and Ethical Boundaries

CertifyLK is an **educational readiness preparation tool**, designed to help micro-, small-, and medium-sized Sri Lankan food manufacturers understand certification pathways, navigate requirements, identify preparation gaps, and view deterministic cost roadmaps.

> [!IMPORTANT]
> **Authoritative Disclaimers & Non-Goals:**
> - CertifyLK is **never** an issuer, auditor, legal adviser, guarantee, or replacement for the Sri Lanka Standards Institution (SLSI), Consumer Affairs Authority (CAA), Ministry of Health, or accredited analytical laboratories.
> - The pilot does **not** evaluate official certification eligibility, regulatory approvals, legal compliance status, or laboratory test conformity.
> - Current catalogue items are marked `content_verified=false` pending qualified food-safety/standards authority review.

---

## 2. Participant Criteria & Recruitment

The controlled pilot is designed for **2–3 Sri Lankan food manufacturers** and at least **1 qualified food safety/certification reviewer**:

### A. Manufacturer Participant Criteria
1. Active micro- or small-to-medium food enterprise operating in Sri Lanka.
2. Produces or plans to produce Fresh Fruit Cordial (or closely related fruit beverage).
3. Representative able to describe the enterprise's real manufacturing process steps, hygiene practices, and recordkeeping.
4. Willing to review readiness guidance, gap analyses, and cost roadmaps.
5. **No mandatory upload requirement:** Participants are not required to upload confidential or sensitive commercial documents to participate.

### B. Domain Reviewer Qualifications
- Qualified food safety specialist, food technologist, lead auditor (ISO 22000 / HACCP / GMP), or standards consultant with practical experience in Sri Lankan food manufacturing regulations and SLSI certification procedures.

---

## 3. Pilot Modes & Data Governance

| Feature | Mode 1: Low-Risk Walkthrough | Mode 2: Consented Real-Evidence Pilot |
|---|---|---|
| **Objective** | Usability, requirement relevance, and roadmap evaluation | Full pipeline verification including evidence analysis |
| **Profile** | Real business characteristics | Real business characteristics |
| **Process** | Manufacturer's real production process steps | Manufacturer's real production process steps |
| **Evidence** | Synthetic / redacted demonstration records | Selected consented business records (redacted) |
| **Privacy Consent** | Standard pilot usability agreement | Signed [PRIVACY_AND_CONSENT.md](PRIVACY_AND_CONSENT.md) protocol |
| **Confidentiality** | Low risk; zero commercial secrets collected | Minimal data; PII and financial records redacted |

---

## 4. Pilot Workflow & Step-by-Step Execution

1. **Pre-Session Briefing:** Explain CertifyLK's role as an educational preparation tool; review disclaimers and obtain participant consent.
2. **Pseudonymous Assignment:** Assign a pilot identifier (e.g. `PILOT-MFG-001`). Real business and personal identities remain strictly off-host and outside Git repositories.
3. **Track 1 Selection:** Start assessment through Product Quality $\rightarrow$ Fresh Fruit Cordial.
4. **Business Profile:** Input years operating, enterprise scale, target market (domestic supermarkets / retail / export), and licensing status.
5. **Applicability Evaluation:** Review recommended certification scheme (`SLS_MARK_CORDIAL`), confidence level, reasoning, and unverified content banner.
6. **Requirement Review:** Browse scheme requirements, category allocations, safety-critical tags, and legal/market tiers in the Assessment Hub.
7. **Production Process Walkthrough:**
   - Manufacturer describes their *actual* process steps (e.g., raw fruit intake $\rightarrow$ washing/peeling $\rightarrow$ extraction $\rightarrow$ cooking/brix formulation $\rightarrow$ pasteurization $\rightarrow$ hot filling $\rightarrow$ cooling $\rightarrow$ labeling/storage).
   - *Note:* Do not force a single hardcoded process; allow authentic variation.
8. **Evidence Plan & Review:** Review requested evidence expectations; upload synthetic, redacted, or consented evidence (or select *Unavailable*).
9. **Clarification Planning:** Answer adaptive clarification questions generated for unresolved requirements (or verify zero-question transition).
10. **Readiness Report Generation:** Review deterministic readiness score indicator, confirmed strengths, potential gaps, and unverified unknowns.
11. **Cost Roadmap Review:** Review categorized fee summary (*Certification Body Fee*, *Laboratory Testing Fee*, *Business Capex*, *Business Opex*), source notes, and quote-required items.
12. **Domain Expert Review:** Qualified reviewer independently reviews CertifyLK output against manufacturer reality and primary sources.
13. **Feedback & Discrepancy Logging:** Record findings in [PILOT_FEEDBACK_REGISTER.md](PILOT_FEEDBACK_REGISTER.md).

---

## 5. Domain Expert Evaluation Procedure

For every reviewed requirement, observation, and roadmap action, the domain expert completes the following verification matrix:

1. **Requirement Mapping:** Did CertifyLK map the manufacturer's input to the correct standard clauses under SLS 187 / SLS 143 / Food Act?
2. **Evidence Polarity:** Did the AI/deterministic observation assign appropriate polarity (`supports`, `concern`, `unclear`) without declaring official compliance findings?
3. **Gap Validity:** Are identified gaps legitimate preparation shortcomings for SLSI audits?
4. **Readiness Score:** Is the score indicator a fair, bounded representation of preparation state?
5. **Cost Category Accuracy:** Are fee schedules categorized correctly into body fees, lab fees, and business improvement capex/opex?
6. **Quote Required Honesty:** Are unpriced or custom quotation items labeled *Quote required* rather than LKR 0?

---

## 6. Manufacturer Qualitative Usefulness Questionnaire

Following the session, the participant is asked 8 qualitative questions:

1. *Did you understand which certification pathway CertifyLK recommended and why?*
2. *Were the evidence requests (photos, logs, test records) relevant to your everyday operation?*
3. *Did the identified preparation gaps highlight practical areas for improvement in your factory?*
4. *Did the prioritized roadmap clarify what steps to take first before contacting SLSI?*
5. *Were the categorized cost estimates (application fees, laboratory tests, equipment) clear and useful for budgeting?*
6. *Did any part of the tool make you feel it was guaranteeing or issuing certification?*
7. *What critical information did you expect to see that was missing?*
8. *Would you recommend this preparation tool to other food manufacturers in your sector?*

---

## 7. Controlled Expansion Gating Criteria

CertifyLK will **not** expand to a 2nd food product or additional certification scheme until all 10 expansion gates are formally satisfied:

- [ ] **Gate 1:** Pilot completed with 2–3 Fresh Fruit Cordial manufacturers.
- [ ] **Gate 2:** Qualified food safety reviewer has completed independent review.
- [ ] **Gate 3:** Zero unresolved **CRITICAL** domain discrepancies in [PILOT_FEEDBACK_REGISTER.md](PILOT_FEEDBACK_REGISTER.md).
- [ ] **Gate 4:** Authoritative primary-source pack (e.g. SLSI specification, Food Act regulations) lawfully secured and documented.
- [ ] **Gate 5:** Versioned catalogue revision prepared with verified clause citations.
- [ ] **Gate 6:** Fee schedules verified against published body schedules or explicitly marked `is_quote_required=true`.
- [ ] **Gate 7:** Deterministic scoring, weighting, and N/A normalization unit tests passing.
- [ ] **Gate 8:** Full API lifecycle and Playwright E2E browser journeys passing for the new scope.
- [ ] **Gate 9:** Data privacy, retention, and evidence handling verified for any new evidence types.
- [ ] **Gate 10:** Production deployment, disaster recovery, and release SHA invariants verified.
