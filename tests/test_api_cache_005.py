MANIFEST_PATH = "/api/v1/manifest"


def test_api_cache_etag_behavior(api_client, auth_header):
    r1 = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r1.status_code == 200

    etag = r1.headers.get("ETag")
    assert etag, "ETag должен присутствовать"

    headers = auth_header.copy()
    headers["If-None-Match"] = etag

    r2 = api_client.get(MANIFEST_PATH, headers=headers)

    # 304 допускается, если контрактом предусмотрено
    assert r2.status_code in (200, 304)

    if r2.status_code == 304:
        assert not r2.content, "304 не должен содержать тело ответа"
