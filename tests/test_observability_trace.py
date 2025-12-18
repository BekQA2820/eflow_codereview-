MANIFEST = "/api/v1/manifest"


def test_observability_headers(api_client, auth_header):
    r = api_client.get(MANIFEST, headers=auth_header)

    assert r.status_code == 200
    assert "X-Request-ID" in r.headers
    assert r.headers["X-Request-ID"] != ""
