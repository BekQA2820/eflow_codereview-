MANIFEST_PATH = "/api/v1/manifest"


def test_api_perf_gzip_support(api_client, auth_header):
    headers = auth_header.copy()
    headers["Accept-Encoding"] = "gzip"

    r = api_client.get(MANIFEST_PATH, headers=headers)
    assert r.status_code == 200
    assert r.headers.get("Content-Encoding") == "gzip"
