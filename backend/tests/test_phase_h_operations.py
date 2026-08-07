def test_health_endpoint_response_schema(client):
    """Verify GET /api/v1/health returns status, service, version, and release_sha without exposing secrets."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data
    assert "version" in data
    assert "release_sha" in data

    # Verify zero secrets or database host details are exposed
    keys = set(data.keys())
    assert keys == {"status", "service", "version", "release_sha"}


def test_ready_endpoint_database_liveness(client):
    """Verify GET /api/v1/ready returns database liveness state."""
    response = client.get("/api/v1/ready")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "ok"
