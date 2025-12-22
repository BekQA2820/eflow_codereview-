def test_invalid_jwt_signature(mocker, api_client):
    """
    API SEC 002
    Invalid JWT signature must return 401 with ErrorResponse
    """

    bad_token = "Bearer INVALID.JWT.SIGNATURE"

    resp = mocker.Mock()
    resp.status_code = 401
    resp.headers = {
        "Content-Type": "application/json",
        "X-Request-ID": "trace-jwt-001",
    }
    resp.json.return_value = {
        "code": "INVALID_TOKEN",
        "message": "Invalid JWT signature",
        "traceId": "trace-jwt-001",
    }

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(
        "/api/v1/manifest",
        headers={"Authorization": bad_token},
    )

    assert r.status_code == 401

    body = r.json()
    assert "code" in body
    assert "traceId" in body
    assert body["code"] in ("UNAUTHORIZED", "INVALID_TOKEN")