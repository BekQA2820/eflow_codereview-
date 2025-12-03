MANIFEST_PATH = "/api/v1/manifest"

def test_api_cache_layout_independent(api_client, auth_header):

    r1 = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r1.status_code == 200

    layout_before = r1.json().get("layout")

    # TODO: изменить только widgets.yaml в S3

    r2 = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r2.status_code == 200

    layout_after = r2.json().get("layout")

    # Пока нет точной спецификации - проверяем детерминированность
    assert layout_before == layout_after
