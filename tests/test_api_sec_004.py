
INVALID_HEADER = {"Authorization": "Bearer WRONG_TOKEN"}
MANIFEST_PATH = "/api/v1/manifest"


def test_api_sec_error_response_format(api_client):
    r = api_client.get(MANIFEST_PATH, headers=INVALID_HEADER)

    assert r.status_code in (401, 403)

    body = r.json()

    assert isinstance(body.get("code"), str)
    assert isinstance(body.get("message"), str)
    assert isinstance(body.get("details"), list)
    assert isinstance(body.get("traceId"), str)

    # Должен быть X-Request-ID
    assert "X-Request-ID" in r.headers
