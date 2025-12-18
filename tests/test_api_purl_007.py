def test_rate_limit_burst_requests(mocker, api_client):
    limit = 60
    state = {"count": 0}

    def fake_get(url, headers=None, **kwargs):
        resp = mocker.Mock()
        state["count"] += 1

        if state["count"] > limit:
            resp.status_code = 429
            resp.headers = {"Retry-After": "2"}
            resp.json.return_value = {"code": "RATE_LIMIT_EXCEEDED"}
        else:
            resp.status_code = 200
            resp.headers = {"X-RateLimit-Remaining": str(limit - state["count"])}
            resp.json.return_value = {"ok": True}

        return resp

    mocker.patch("requests.get", side_effect=fake_get)

    last_response = None
    for _ in range(61):
        last_response = api_client.get(
            "/api/v1/manifest",
            headers={"Authorization": "Bearer token-burst"},
        )

    assert last_response.status_code == 429
    assert "Retry-After" in last_response.headers
    assert int(last_response.headers["Retry-After"]) > 0
