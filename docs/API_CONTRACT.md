# API contract

Base URL: `http://localhost:8000/api/v1`. JSON responses include `X-Request-ID`; clients may supply the same header. UUIDs below are abbreviated examples. Timestamps are RFC 3339 UTC.

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

Statuses: `200`, `404`, `422` for malformed UUID.

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
{"stages":[{"position":1,"name":"Ingredient receiving","tags":["receiving","supplier_control"],"confidence":0.92}],"uncertainties":["Cooking endpoint measurement is unclear"]}
```

### `POST /assessments/{assessment_id}/evidence-plan`

No body. Requires process analysis. `200`:

```json
{
  "status":"evidence_pending",
  "requests":[
    {"id":"2c8b29b1-d828-48de-89f4-acd6f4679d65","evidence_type":"production_area","kind":"photo","title":"Production area","required":false,"status":"requested"},
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

### `POST /assessments/{assessment_id}/evidence-analysis`

No body. All slots must be uploaded or unavailable. `200`:

```json
{
  "status":"evidence_complete",
  "observations":[{"id":"28f89fd5-7c4b-4dc3-a926-341ccb039506","evidence_request_id":"...","requirement_id":"HYG_HANDWASH","polarity":"supports","text":"A dedicated handwashing area is visible.","confidence":0.86}]
}
```

Returns `409` while requests remain unresolved; `502` for AI failure without fallback.

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

No body. Requires `ready_to_score`. Performs deterministic evaluation/scoring/roadmap creation in one transaction; AI can only explain fixed items. `200`:

```json
{"status":"completed","result":{"overall_score_raw":"47.5000","overall_score":48,"evidence_completeness":55,"roadmap_count":8}}
```

Calling this endpoint for an already completed assessment is idempotent and returns the stored summary. Returns `409` if incomplete.

### `GET /assessments/{assessment_id}/result`

Requires a completed result. `200` (abridged):

```json
{
  "assessment_id":"149692e0-b9fd-4b83-b4c5-246f921b1715",
  "overall_score_raw":"47.5000",
  "overall_score":48,
  "evidence_completeness":55,
  "category_scores":[{"category":"hygiene_sanitation","label":"Hygiene and sanitation","score_raw":"12.5000","score":63,"weight":20}],
  "strengths":[{"requirement_id":"HYG_SURFACE","title":"Cleanable production surfaces","status":"confirmed","evidence_references":["profile.production_location"]}],
  "gaps":[{"requirement_id":"DOC_BATCH","title":"Batch production records","status":"gap","evidence_references":["answer.DOC_BATCH_01"]}],
  "unknowns":[{"requirement_id":"PROC_TEMP","title":"Measured cooking endpoint","status":"unknown","evidence_references":["process.3"]}],
  "roadmap":[{"recommendation_id":"REC_BATCH_RECORD","title":"Create batch-production record","priority":2,"one_time_cost":{"min":0,"max":1500,"currency":"LKR"},"recurring_cost":{"min":0,"max":300,"currency":"LKR"},"expected_gain":4.0,"projected_score":52,"explanation":"Record each batch so ingredients, cooking and output can be traced."}],
  "cost_summary":{"one_time_min":0,"one_time_max":25000,"recurring_min":0,"recurring_max":5000,"currency":"LKR"},
  "disclaimer":"CertifyLK is a readiness-assessment tool and does not issue, guarantee, or replace SLS certification."
}
```

Returns `409` when the assessment is not completed and `404` when no assessment/result exists.
