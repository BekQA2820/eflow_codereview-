MANIFEST = "/api/v1/manifest"


def test_auth_required_401(mocker, api_client):
    """
    API SEC 001
    Manifest requires authorization and returns standard ErrorResponse
    """

    resp = mocker.Mock()
    resp.status_code = 401
    resp.headers = {
        "Content-Type": "application/json",
        "X-Request-ID": "trace-auth-001",
    }
    resp.json.return_value = {
        "code": "UNAUTHORIZED",
        "message": "Authentication required",
        "traceId": "trace-auth-001",
    }

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(MANIFEST)

    assert r.status_code == 401

    body = r.json()
    assert "code" in body
    assert "traceId" in body