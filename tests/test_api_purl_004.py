def test_rate_limit_applies_per_token_not_ip(mocker, api_client):
    ok_resp = mocker.Mock()
    ok_resp.status_code = 200
    ok_resp.headers = {"X-RateLimit-Remaining": "1"}
    ok_resp.json.return_value = {"ok": True}

    limit_resp = mocker.Mock()
    limit_resp.status_code = 429
    limit_resp.headers = {"Retry-After": "1"}
    limit_resp.json.return_value = {"code": "RATE_LIMIT_EXCEEDED"}

    def fake_get(url, headers=None, **kwargs):
        token = headers.get("Authorization")
        if token == "Bearer token-a":
            fake_get.calls_a += 1
            return limit_resp if fake_get.calls_a > 60 else ok_resp
        return ok_resp

    fake_get.calls_a = 0

    mocker.patch("requests.get", side_effect=fake_get)

    for _ in range(61):
        r = api_client.get("/api/v1/manifest", headers={"Authorization": "Bearer token-a"})

    assert r.status_code == 429

    r_other = api_client.get(
        "/api/v1/manifest",
        headers={"Authorization": "Bearer token-b"},
    )

    assert r_other.status_code == 200
