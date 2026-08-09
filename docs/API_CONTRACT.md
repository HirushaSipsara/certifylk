# API contract

Local base URL: `http://localhost:8000/api/v1`. Production uses same-origin `https://<production-domain>/api/v1` through Nginx. JSON responses include `X-Request-ID`; clients may supply the same header. UUIDs below are abbreviated examples. Timestamps are RFC 3339 UTC. Production and local deployments use the same response shapes.

Process-analysis, evidence-analysis, and applicability responses include read-only execution metadata from the exact successful `ai_runs` record created during that request. `provider` is `gemini` or `mock`. `fallback_used=true` means the primary Gemini path failed and the configured Mock fallback completed the operation. Internal retry attempts are not exposed as live API state.

Evidence analysis is optional and bounded independently from applicability AI. Uploaded files are reviewed one at a time, with one provider attempt per file, an eight-second per-file budget, and a twenty-second total request budget by default. Evidence review does not use Mock fallback: a provider timeout/failure leaves that file without an AI observation and returns a controlled `200` response so the saved self-assessment can continue. Successful file observations are preserved. Each returned observation carries its exact successful provider and validation metadata.

The API is transitional. The legacy four-page endpoints remain operational against the global readiness catalogue. The knowledge-base/applicability endpoints select a certification scheme and expose its requirement overview, but certificate-specific evidence/evaluation/result contracts are not yet complete. Planned endpoints or fields are documented only in `FULL_IMPLEMENTATION_PLAN.md`, not as current API behavior.

## Shared errors

```json
{
  "error": {
    "code": "invalid_transition",
    "message": "Process cannot be saved before the profile is complete.",
    "details": [{"field": "status", "message": "Expected profile_complete"}],
    "request_id": "b93b8e1c-3de9-4c96-8c60-46cb8ac78c55"
  }
}
```

All endpoints may return `500` (`internal_error`). Resource endpoints return `404`. Workflow-state violations return `409`. JSON/body validation returns `422`, with `details` mapped to fields. Uploads additionally return `413` or `415`.

## System

### `GET /health`

Process liveness. `200`:

```json
{"status":"ok","service":"CertifyLK API"}
```

### `GET /ready`

Checks database connectivity. `200` when ready, `503` with the shared envelope otherwise.

```json
{"status":"ready","database":"ok"}
```

## Assessments

### `POST /assessments`

Creates a guest assessment. Empty JSON body is optional. `201`:

```json
{"id":"ed092776-3b93-4fb7-b475-5216925f0d0c","status":"draft_profile","current_page":"profile","created_at":"2026-08-05T12:00:00Z"}
```

### `GET /assessments/{assessment_id}`

Returns resumable state and assigned questions/evidence requests. `200`:

```json
{
  "id":"ed092776-3b93-4fb7-b475-5216925f0d0c",
  "status":"evidence_pending",
  "current_page":"evidence",
  "profile":{"product_name":"Chilli paste","food_category":"processed_food"},
  "process_steps":[{"position":1,"text":"Purchase chillies"}],
  "assigned_questions":[],
  "evidence_requests":[{"id":"2c8b29b1-d828-48de-89f4-acd6f4679d65","evidence_type":"product_label","kind":"document","status":"requested"}]
}
```

Statuses: `200`, `404`, `422` for malformed UUID. Implemented assessment status values are `draft_profile`, `profile_complete`, `process_complete`, `evidence_pending`, `evidence_complete`, `clarification_pending`, `ready_to_score`, `completed`, and `failed`.

### `POST /assessments/sample`

Creates a new completed sample through the normal deterministic result engine. `201` returns:

```json
{"id":"149692e0-b9fd-4b83-b4c5-246f921b1715","status":"completed","current_page":"result","result_url":"/assessment/149692e0-b9fd-4b83-b4c5-246f921b1715/result"}
```

## Page 1 — profile

### `PUT /assessments/{assessment_id}/profile`

```json
{
  "product_name":"Homemade chilli paste",
  "food_category":"processed_food",
  "other_category_text":null,
  "production_location":"home_kitchen",
  "production_location_other":null,
  "production_scale":"small",
  "worker_range":"1_5",
  "packaging_type":"glass_bottle",
  "storage_method":"room_temperature",
  "shelf_life_range":"one_to_six_months",
  "existing_certification":"none",
  "production_record_frequency":"sometimes",
  "additional_information":"Cooked in small batches."
}
```

`200` returns `{"status":"profile_complete","profile":{...}}`. Returns `409` if the assessment is beyond an editable profile state and `422` when required values or conditional Other text are missing.

### `POST /assessments/{assessment_id}/adaptive-plan`

No body. Requires `profile_complete`. `200`:

```json
{
  "questions":[
    {"id":"PROC_TEMP_01","text":"How do you decide that cooking is complete?","options":[{"value":"thermometer","label":"Measure temperature"},{"value":"time","label":"Use time only"}],"allows_other":true}
  ]
}
```

Returns `409` for an invalid transition and `502` for AI failure without fallback.

## Page 2 — process

### `PUT /assessments/{assessment_id}/process`

```json
{
  "steps":["Purchase ingredients","Wash and prepare","Cook mixture","Fill bottles","Store and distribute"],
  "adaptive_answers":[{"question_id":"PROC_TEMP_01","value":"time","other_text":null}]
}
```

Exactly five strings are required; at least three must contain text. Every answer must reference an assigned adaptive question and use an approved option or allowed Other. `200` returns `{"status":"process_complete"}`; `409`/`422` as above.

### `POST /assessments/{assessment_id}/process-analysis`

No body. Requires `process_complete`. `200`:

```json
{"stages":[{"position":1,"name":"Ingredient receiving","tags":["receiving","supplier_control"],"confidence":0.92}],"uncertainties":["Cooking endpoint measurement is unclear"],"provider":"gemini","fallback_used":false}
```

### `POST /assessments/{assessment_id}/evidence-plan`

No body. Requires process analysis. `200`:

```json
{
  "status":"evidence_pending",
  "requests":[
    {"id":"2c8b29b1-d828-48de-89f4-acd6f4679d65","evidence_type":"production_area","kind":"photo","title":"Production area","required":false,"status":"requested","requirement_id":"SLS_HYG_HANDWASH","current_state_question":"Is this currently in place in your operation? Suitable handwashing facilities...","self_assessment":null},
    {"id":"7547e7c9-9017-4567-93d5-ebfdfd5a4ea2","evidence_type":"product_label","kind":"document","title":"Product label","required":false,"status":"requested"}
  ]
}
```

The response never exceeds five photos or two documents.

## Page 3 — evidence

### `POST /assessments/{assessment_id}/evidence/upload`

Multipart fields: `evidence_request_id` (UUID) and `file`. The request must belong to the assessment. Accepted images: JPEG, PNG, WebP up to `MAX_IMAGE_MB`; documents: PDF up to `MAX_PDF_MB`. `201`:

```json
{"file_id":"46870ed7-fb61-4b95-8190-d0547f678a29","evidence_request_id":"2c8b29b1-d828-48de-89f4-acd6f4679d65","status":"uploaded","content_type":"image/jpeg","size_bytes":245012}
```

Returns `409` for closed/wrong-stage slots, `413` oversized, `415` unsupported or mismatched type, and `422` malformed multipart data.

### `PUT /assessments/{assessment_id}/evidence/{evidence_request_id}/unavailable`

No body. `200`: `{"evidence_request_id":"...","status":"unavailable"}`. Returns `409` if already uploaded/analyzed or transition is invalid.

### `PUT /assessments/{assessment_id}/evidence/{evidence_request_id}/self-assessment`

Stores the controlled, requirement-specific current-state response independently from file status:

```json
{"value":"yes"}
```

Allowed values are `yes`, `partial`, `no`, and `not_sure`. `200`: `{"evidence_request_id":"...","value":"yes"}`. These responses are self-reported readiness inputs and never count as accepted uploaded evidence.

### `DELETE /assessments/{assessment_id}/evidence/{evidence_request_id}`

Resets an uploaded or unavailable evidence slot to `requested` before evidence
analysis. Any stored file for the slot is deleted through the storage provider,
so the user can safely upload a replacement or choose “I do not have this”
again. `200`: `{"evidence_request_id":"...","status":"requested"}`. Returns
`404` for an unknown slot and `409` when the assessment has advanced past the
evidence stage.

### `POST /assessments/{assessment_id}/evidence-analysis`

No body. For scheme assessments, every current-state question must be answered; uploads are optional. `200`:

```json
{
  "status":"evidence_complete",
  "provider":"gemini",
  "fallback_used":false,
  "review_status":"partial",
  "message":"AI evidence review is temporarily unavailable for one or more uploaded files. Your files and self-assessment answers are saved, and you may continue.",
  "failed_evidence_request_ids":["7547e7c9-9017-4567-93d5-ebfdfd5a4ea2"],
  "observations":[{"id":"28f89fd5-7c4b-4dc3-a926-341ccb039506","evidence_request_id":"...","requirement_id":"HYG_HANDWASH","polarity":"supports","text":"A dedicated handwashing area is visible.","confidence":0.86,"provider":"gemini","fallback_used":false,"validation_status":"validated"}]
}
```

Each observation retains its validated polarity (`supports`, `concern`, or `unclear`), confidence value, and exact execution provenance. The UI presents `>=0.80` as Clear, `>=0.50` as Plausible, and lower values as Unclear without changing the stored number. Older clients may ignore the added read-only provenance fields.

`review_status` is `complete`, `partial`, `unavailable`, or `not_requested`. Provider metadata is nullable when no successful AI review occurred. A provider failure does not fabricate a Mock observation and does not block clarification. Returns `409` while current-state responses remain unanswered and `400` when a stored file is missing.

### `POST /assessments/{assessment_id}/clarification-plan`

No body. Requires `evidence_complete`. `200`:

```json
{"status":"clarification_pending","questions":[{"id":"DOC_BATCH_01","text":"Do you assign a batch code?","options":[{"value":"always","label":"Always"},{"value":"sometimes","label":"Sometimes"},{"value":"never","label":"Never"}],"allows_other":false}]}
```

Exactly three to five approved questions are returned.

## Page 4 and result

### `PUT /assessments/{assessment_id}/clarifications`

```json
{"answers":[{"question_id":"DOC_BATCH_01","value":"sometimes","other_text":null}]}
```

All assigned clarification questions require valid answers. `200`: `{"status":"ready_to_score"}`. Returns `409` in the wrong state and `422` for missing/unassigned/invalid options.

### `POST /assessments/{assessment_id}/complete`

No body. Requires `ready_to_score`. Performs deterministic evaluation/scoring/roadmap creation in one transaction; AI can only explain fixed items. Assessments with `scheme_id` use the frozen `scheme_requirements`, `certification_scheme.category_weights`, and `scheme_cost_items`; legacy assessments without `scheme_id` use the global regression catalogue. `200`:

```json
{"status":"completed","result":{"overall_score_raw":"47.5000","overall_score":48,"evidence_completeness":55,"roadmap_count":8}}
```

Calling this endpoint for an already completed assessment is idempotent and returns the stored summary. Returns `409` if incomplete.

Readiness and evidence completeness are independent. Approved profile/process answers can contribute to deterministic requirement readiness when a scheme requirement has a matching controlled `evaluation_rule`; only accepted evidence-observation references contribute to `evidence_completeness`. The result groups `confirmed` requirements under `strengths`, `gap`/`partial` under `gaps`, and insufficiently verified requirements under `unknowns`.

Returns `409` when the assessment is not completed and `404` when no assessment/result exists. The result payload includes nullable `scheme_id`; certificate-scoped assessments expose the selected scheme, while legacy assessments may leave it null.

## Certification Knowledge Base & Applicability

### `GET /categories`

List enabled product categories. `200`:

```json
[
  {
    "id": "11111111-1111-1111-1111-111111111111",
    "name": "Food Products",
    "slug": "food_products",
    "description": "Manufactured food and beverage products for sale in Sri Lanka.",
    "display_order": 1
  }
]
```

### `GET /categories/{category_id}/products`

List enabled products for a category. `200`:

```json
[
  {
    "id": "22222222-2222-2222-2222-222222222222",
    "name": "Fresh Fruit Cordial",
    "slug": "fresh_fruit_cordial",
    "description": "A sweetened, dilutable fruit drink concentrate made from fresh fruit juice, sugar, water, and permitted preservatives.",
    "category_id": "11111111-1111-1111-1111-111111111111",
    "display_order": 1
  }
]
```

### `GET /schemes`

List certification schemes, optionally filtered by `?track=product_quality` or `?track=process_management`. `200`:

```json
[
  {
    "id": "SLS_MARK_CORDIAL",
    "name": "SLS Mark — Fresh Fruit Cordial",
    "short_code": "SLS_MARK",
    "track": "product_quality",
    "mandatory_tier": "market_required",
    "standard_version": "draft-2026-08",
    "catalogue_revision": "2026-08-07-draft",
    "summary": "The SLS Mark certifies that your product consistently meets the Sri Lanka Standard for Fresh Fruit Cordial (SLS 187).",
    "typical_timeline_days": 365,
    "body_name": "Sri Lanka Standards Institution",
    "active": true
  }
]
```

### `GET /schemes/{scheme_id}/requirements`

List clauses/requirements for a certification scheme. `200`:

```json
[
  {
    "id": "SLS_HYG_HANDWASH",
    "scheme_id": "SLS_MARK_CORDIAL",
    "category_label": "Hygiene & Sanitation",
    "title": "Handwashing facilities and supplies",
    "description": "Suitable handwashing facilities with soap and hygienic drying must be accessible to all production staff at all times.",
    "weight": 6.0,
    "safety_critical": true,
    "source_document": "SLS 187 / GMP Guidelines (SLSI)",
    "source_document_id": "SRC_SLS_187_CORDIAL_DRAFT",
    "clause_reference": "Clause 4.2.1 — Personal Hygiene",
    "source_url": "",
    "content_verified": false,
    "standard_version": "draft-2026-08",
    "effective_date": "2026-08-07",
    "display_order": 1
  }
]
```

### `GET /schemes/{scheme_id}/evidence-expectations`

List curated evidence expectations tied to a certification scheme’s requirements. `200`:

```json
[
  {
    "id": "EV_SLS_HYG_HANDWASH",
    "scheme_id": "SLS_MARK_CORDIAL",
    "requirement_id": "SLS_HYG_HANDWASH",
    "kind": "photo",
    "label": "Evidence for Handwashing facilities and supplies",
    "guidance_text": "Provide available evidence for this requirement, or mark it unavailable.",
    "required": true,
    "display_order": 1
  }
]
```

### `POST /business-profiles`

Create a screening business profile. Optional `assessment_id` links the profile to an existing guest assessment; optional `product_slug` links a Track 1 product. Omitting `product_slug` supports Track 2. `201`:

```json
{
  "name": "Lanka Cordial Works",
  "business_type": "limited_company",
  "years_operating": 3,
  "scale": "small",
  "market": ["supermarket", "export"],
  "existing_certifications": [],
  "has_food_licence": "yes",
  "monthly_volume_range": "1000_5000_litres",
  "additional_info": "We want to enter formal retail.",
  "assessment_id": "60609be3-b36a-4455-95d9-31898586ee9f",
  "product_slug": "fresh_fruit_cordial"
}
```

Response:

```json
{
  "id": "d5bffaac-988d-4977-9770-870fa53295f7",
  "name": "Lanka Cordial Works",
  "business_type": "limited_company",
  "scale": "small",
  "market": ["supermarket", "export"],
  "has_food_licence": "yes"
}
```

### `POST /assessments/{assessment_id}/applicable-schemes`

Runs the Applicability Reasoning operation on the linked business profile. Track is inferred: an assessment with a product uses `product_quality`; without a product it uses `process_management`. Candidates are loaded from PostgreSQL, already-held Food Business Registration is deterministically removed from the action candidates, all AI output IDs are whitelisted, and the recommended ID is stored on the assessment. Returns ranked actionable decisions, separately acknowledged already-held pathways, AI reasoning, and supplied source references. `200`:

```json
{
  "assessment_id": "60609be3-b36a-4455-95d9-31898586ee9f",
  "overall_reasoning": "Based on the submitted business profile...",
  "recommended_path_scheme_id": "SLS_MARK_CORDIAL",
  "decisions": [
    {
      "scheme_id": "SLS_MARK_CORDIAL",
      "tier": "market_required",
      "confidence": 0.92,
      "reasoning": "The target market includes supermarket channels...",
      "source_reference": "applicability_rule.mandatory_note",
      "scheme_name": "SLS Mark — Fresh Fruit Cordial",
      "body_name": "Sri Lanka Standards Institution",
      "typical_timeline_days": 365,
      "summary": "SLS Mark readiness for Fresh Fruit Cordial."
    }
  ],
  "already_held_schemes": [
    {
      "scheme_id": "CAA_FOOD_REG",
      "scheme_name": "CAA Food Business Registration",
      "body_name": "Consumer Affairs Authority",
      "status_message": "Your business profile says this registration or licence is already held, so it is not recommended as a new action."
    }
  ],
  "provider": "mock",
  "fallback_used": false,
  "has_unverified_content": true
}
```

The current operation receives DB-sourced scheme facts and the saved optional profile narrative in a bounded provider call. `already_held_schemes` is deterministic read-only metadata, not model output. The response does not claim that Gemini function/tool calling occurred. `has_unverified_content` reflects the selected recommended scheme’s current requirement rows.

### `GET /assessments/{assessment_id}/scheme-requirements`

Returns requirements for the scheme linked to an assessment. `200`:

```json
[
  {
    "id": "SLS_HYG_HANDWASH",
    "scheme_id": "SLS_MARK_CORDIAL",
    "category_label": "Hygiene & Sanitation",
    "title": "Handwashing facilities and supplies",
    "description": "Suitable handwashing facilities...",
    "weight": 6.0,
    "safety_critical": true,
    "source_document": "SLS 187 / GMP Guidelines (SLSI)",
    "clause_reference": "Clause 4.2.1 — Personal Hygiene",
    "source_url": "",
    "content_verified": false,
    "display_order": 1
  }
]
```
