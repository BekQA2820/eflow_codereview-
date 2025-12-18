MANIFEST = "/api/v1/manifest"


def test_auth_required_401(api_client):

    r = api_client.get(MANIFEST)
    assert r.status_code == 401, "Manifest must require authorization"

    # Standard error response
    body = r.json()
    assert "code" in body
    assert "traceId" in body
