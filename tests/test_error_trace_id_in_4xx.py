def test_trace_id_for_4xx_errors(api_client):
    response = api_client.get("/api/v1/manifest")  # no auth header

    assert response.status_code in (401, 403)

    body = response.json()
    assert "traceId" in body, "traceId must be present for all errors"
    assert "code" in body
    assert "message" in body
