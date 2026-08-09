# CertifyLK Pilot Privacy, Data Governance & Consent Protocol

**Document Version:** 1.0.0 (Phase I Protocol)  
**Governance Scope:** Pilot Participants, Domain Reviewers, and Demonstration Users  
**System Architecture Reference:** [docs/ARCHITECTURE.md](ARCHITECTURE.md)

---

## 1. Purpose of Data Collection

CertifyLK collects business process details, manufacturing profiles, and operational evidence strictly for the purpose of **educational certification readiness preparation**. The tool provides gap analyses, preparation roadmaps, and deterministic fee estimates to help Sri Lankan food producers evaluate their readiness before approaching official bodies such as the Sri Lanka Standards Institution (SLSI) or the Consumer Affairs Authority (CAA).

---

## 2. Information Collected & Processing Boundaries

### A. Business Profile & Process Data
- **Information Collected:** Enterprise scale (micro/small/medium), operational years, target markets (domestic retail, supermarkets, export), existing licences, and steps in the production process.
- **Processing Purpose:** To identify applicable certification pathways and map factory practices to relevant standards requirements under SLS 187, SLS GMP, SLS HACCP, and ISO 22000.

### B. Evidence Submissions (Photos, Documents, Test Records)
- **Information Collected:** Photos of manufacturing facilities (washing areas, filling rooms, storage), batch record sheets, water testing reports, and pest control logs.
- **Processing Purpose:** To extract observations with polarity (`supports`, `concern`, `unclear`) and determine preparation status.

---

## 3. Data Minimization & Redaction Guidelines

> [!IMPORTANT]
> **Participant Protection & Confidentiality Rules:**
> - **Redaction Encouraged:** Participants must redact personal identification (national identity card numbers, private residential addresses), proprietary recipe formulations, trade secrets, and financial account numbers before uploading documents.
> - **Synthetic Evidence Permitted:** In Mode 1 (Low-Risk Walkthrough), synthetic or demonstration records can be used exclusively.
> - **No Mandatory Evidence:** The tool fully supports the option *"I do not have this"* for any requested evidence item without blocking assessment generation.

---

## 4. AI Provider Data Transmission & Boundaries

- **Transmission Scope:** CertifyLK sends only data necessary for the bounded AI operation through the configured backend AI provider (`GeminiAIProvider` / `MockAIProvider`). For evidence analysis in Gemini mode, this includes the selected uploaded image/PDF bytes, MIME type, evidence-request ID, and database-sourced requirement context. Users must therefore upload only synthetic, redacted, or explicitly consented evidence.
- **Credential Isolation:** AI provider credentials (`GEMINI_API_KEY`) reside exclusively in backend environment configuration and are never exposed to the frontend browser or client responses.
- **Architectural Safeguard:** Raw evidence files and uploaded binary content are validated and stored locally on persistent host volumes. A bounded copy is transmitted to Gemini only during requested evidence analysis; it is treated as untrusted data and never as instructions. Raw evidence and document contents are never written to application logs or `ai_runs`.

---

## 5. Storage, Retention & Deletion Capabilities

### A. Server-Side Storage Architecture
- Assessment state, question answers, and completed result snapshots are stored in PostgreSQL on private Docker networks.
- Uploaded evidence files reside in private, non-public storage directories (`UPLOAD_DIR`).
- Backup snapshots are created via automated scripts and staged in secured off-host storage.

### B. Server-Side Deletion Truthfulness
- **Local Dashboard Removal:** The `/my-assessments` page allows users to remove guest assessment UUIDs from their browser's local storage (`localStorage`).
- **Server-Side Status:** *Removing an assessment from the browser dashboard removes the local recovery shortcut only; it does not trigger automated server-side database row deletion or immediate physical erasure of uploaded files.*
- **Retention Lifecycle:** Pilot assessment data and test evidence files are subject to an operational retention period of **30 days**, after which test backups and temporary artifacts are rotated and purged according to retention lifecycle rules.

---

## 6. Participant Consent Agreement (Pilot Mode 2)

Before participating in a live assessment session involving real business documents, the participant confirms:

1. *I understand that CertifyLK is an educational readiness preparation tool and does not issue, guarantee, or replace official certification by SLSI, CAA, or accredited laboratories.*
2. *I agree to provide relevant process descriptions and redacted documentation for the purpose of readiness assessment and research validation.*
3. *I have redacted sensitive commercial formulations, financial records, and personal identification details from all uploaded files.*
4. *I understand that my assessment data will be stored temporarily on secure servers for the duration of the pilot review period.*
5. *I understand that I may withdraw consent or request manual data purging at any time by contacting the CertifyLK research team.*
