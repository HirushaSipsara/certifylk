#!/usr/bin/env bash
set -euo pipefail

api_base="${CERTIFYLK_API_BASE:-http://localhost:8000/api/v1}"
frontend_base="${CERTIFYLK_FRONTEND_BASE:-http://localhost:3000}"

curl --fail --silent "$api_base/health" >/dev/null
curl --fail --silent "$api_base/ready" >/dev/null
curl --fail --silent "$frontend_base" >/dev/null

sample_json="$(curl --fail --silent -X POST "$api_base/assessments/sample")"
assessment_id="$(printf '%s' "$sample_json" | python -c 'import json,sys; print(json.load(sys.stdin)["id"])')"
result_json="$(curl --fail --silent "$api_base/assessments/$assessment_id/result")"

printf '%s' "$result_json" | python -c '
import json, sys
result = json.load(sys.stdin)
assert 0 <= result["overall_score"] <= 100
assert result["strengths"]
assert result["gaps"]
assert result["roadmap"]
assert result["roadmap"][0]["one_time_cost"]["currency"] == "LKR"
assert "does not issue" in result["disclaimer"]
print("Happy path passed: assessment={} score={}".format(result["assessment_id"], result["overall_score"]))
'
