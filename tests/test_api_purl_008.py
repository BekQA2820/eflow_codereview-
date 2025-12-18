def test_rate_limit_recovery_after_retry_after(mocker, api_client):
    state = {"blocked": True}

    def fake_get(url, headers=None, **kwargs):
        resp = mocker.Mock()

        if state["blocked"]:
            resp.status_code = 429
            resp.headers = {"Retry-After": "1"}
            resp.json.return_value = {"code": "RATE_LIMIT_EXCEEDED"}
        else:
            resp.status_code = 200
            resp.headers = {"X-RateLimit-Remaining": "59"}
            resp.json.return_value = {"ok": True}

        return resp

    mocker.patch("requests.get", side_effect=fake_get)

    r1 = api_client.get(
        "/api/v1/manifest",
        headers={"Authorization": "Bearer token-recover"},
    )

    assert r1.status_code == 429
    assert r1.headers["Retry-After"] == "1"

    state["blocked"] = False

    r2 = api_client.get(
        "/api/v1/manifest",
        headers={"Authorization": "Bearer token-recover"},
    )

    assert r2.status_code == 200
    assert r2.headers["X-RateLimit-Remaining"] == "59"
