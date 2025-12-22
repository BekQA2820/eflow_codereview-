def test_trace_id_for_4xx_errors(mocker, api_client):
    """
    API ERROR CONTRACT
    Все 4xx ошибки должны содержать traceId
    """

    resp = mocker.Mock()
    resp.status_code = 401
    resp.headers = {
        "Content-Type": "application/json",
        "X-Request-ID": "trace-4xx-001",
    }
    resp.json.return_value = {
        "code": "UNAUTHORIZED",
        "message": "Authentication required",
        "traceId": "trace-4xx-001",
    }

    # ВАЖНО: мок именно requests.request
    mocker.patch("requests.request", return_value=resp)

    r = api_client.get("/api/v1/manifest")

    assert r.status_code in (401, 403)

    body = r.json()
    assert "traceId" in body
    assert "code" in body
    assert "message" in body
