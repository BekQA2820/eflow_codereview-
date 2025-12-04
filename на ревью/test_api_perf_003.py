MANIFEST_PATH = "/api/v1/manifest"


def test_api_perf_manifest_size_limit(api_client, auth_header):
    r = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r.status_code == 200

    size = len(r.content)
    assert size < 512 * 1024  # 512KB
