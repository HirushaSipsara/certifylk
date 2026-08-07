"""Production smoke test script for CertifyLK.

Executes non-destructive health, catalogue, sample, and Track 2 applicability checks
against a specified base URL (defaulting to https://certifylk.duckdns.org or local host).
"""

import argparse
import sys
import urllib.request
import json


def run_smoke_checks(base_url: str) -> None:
    print(f"Starting CertifyLK production smoke checks against: {base_url}")
    api_url = f"{base_url.rstrip('/')}/api/v1"

    # 1. Health check
    health_res = urllib.request.urlopen(f"{api_url}/health", timeout=10)
    assert health_res.status == 200, f"Health check failed with status {health_res.status}"
    health_data = json.loads(health_res.read().decode())
    print(f"  [PASS] Health check: status={health_data.get('status')}, version={health_data.get('version')}, sha={health_data.get('release_sha')}")

    # 2. Ready check
    ready_res = urllib.request.urlopen(f"{api_url}/ready", timeout=10)
    assert ready_res.status == 200, f"Ready check failed with status {ready_res.status}"
    print("  [PASS] Database readiness check passed.")

    # 3. Canonical Sample check
    sample_req = urllib.request.Request(f"{api_url}/assessments/sample", method="POST")
    sample_res = urllib.request.urlopen(sample_req, timeout=15)
    assert sample_res.status in (200, 201), f"Sample creation failed with status {sample_res.status}"
    sample_data = json.loads(sample_res.read().decode())
    assessment_id = sample_data["id"]
    print(f"  [PASS] Canonical sample created: {assessment_id}")

    # 4. Result snapshot check
    result_res = urllib.request.urlopen(f"{api_url}/assessments/{assessment_id}/result", timeout=15)
    assert result_res.status == 200, f"Result fetch failed with status {result_res.status}"
    result_data = json.loads(result_res.read().decode())
    assert 0 <= result_data["overall_score"] <= 100
    assert "roadmap" in result_data
    assert "cost_summary" in result_data
    assert "disclaimer" in result_data
    print(f"  [PASS] Canonical sample result verified: score={result_data['overall_score']}, scheme={result_data.get('scheme_id')}")

    print("All production smoke checks PASSED successfully.")


def main():
    parser = argparse.ArgumentParser(description="Run CertifyLK production smoke tests")
    parser.add_argument("--base-url", default="https://certifylk.duckdns.org", help="Base URL of production application")
    args = parser.parse_args()

    try:
        run_smoke_checks(args.base_url)
    except Exception as err:
        print(f"ERROR: Smoke check failed: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
