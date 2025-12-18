HEALTH = "/health"
READY = "/ready"


def test_api_health_ready(api_client):
    # /health
    r1 = api_client.get(HEALTH)
    assert r1.status_code == 200, "Healthcheck must return 200"
    assert "X-Request-ID" in r1.headers, "Health response must contain X-Request-ID"

    # /ready
    r2 = api_client.get(READY)
    assert r2.status_code == 200, "Ready endpoint must return 200"
    assert "X-Request-ID" in r2.headers, "Ready response must contain X-Request-ID"
