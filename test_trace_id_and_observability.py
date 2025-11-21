def test_trace_id_and_request_id_present(api_client, auth_header):
    response = api_client.get("/api/v1/manifest", headers=auth_header)

    assert response.status_code == 200

    # трейсинг хедеров
    assert "X-Request-ID" in response.headers

    # body без traceId
    assert "traceId" not in response.json()
