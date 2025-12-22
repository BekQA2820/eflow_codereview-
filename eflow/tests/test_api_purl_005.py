def test_rate_limit_remaining_decreases(mocker, api_client):
    responses = []

    for remaining in ["59", "58", "57"]:
        resp = mocker.Mock()
        resp.status_code = 200
        resp.headers = {"X-RateLimit-Remaining": remaining}
        resp.json.return_value = {"ok": True}
        responses.append(resp)

    mocker.patch("requests.get", side_effect=responses)

    r1 = api_client.get("/api/v1/manifest")
    r2 = api_client.get("/api/v1/manifest")
    r3 = api_client.get("/api/v1/manifest")

    assert r1.headers["X-RateLimit-Remaining"] == "59"
    assert r2.headers["X-RateLimit-Remaining"] == "58"
    assert r3.headers["X-RateLimit-Remaining"] == "57"
