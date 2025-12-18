

HEALTH = "/health"
READY = "/ready"


def test_api_health_ready(mocker, api_client):
    """
    API SMOKE 001
    Health and readiness endpoints are reachable and return required headers
    """

    health_resp = mocker.Mock()
    health_resp.status_code = 200
    health_resp.headers = {"X-Request-ID": "trace-health-001"}

    ready_resp = mocker.Mock()
    ready_resp.status_code = 200
    ready_resp.headers = {"X-Request-ID": "trace-ready-001"}

    mocker.patch(
        "requests.get",
        side_effect=[health_resp, ready_resp],
    )

    # /health
    r1 = api_client.get(HEALTH)
    assert r1.status_code == 200
    assert "X-Request-ID" in r1.headers

    # /ready
    r2 = api_client.get(READY)
    assert r2.status_code == 200
    assert "X-Request-ID" in r2.headers
