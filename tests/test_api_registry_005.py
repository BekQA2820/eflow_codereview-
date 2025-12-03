import pytest

MANIFEST_PATH = "/api/v1/manifest"


@pytest.mark.skip(reason="Требуется доступ к Valkey/Redis TTL и управляемому тестовому widgets.yaml")
def test_api_registry_ttl_refresh(api_client, auth_header):
    r1 = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r1.status_code == 200
    body1 = r1.json()

    # TODO: уменьшить TTL или обнулить через redis_client

    # TODO: дождаться истечения TTL

    r2 = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r2.status_code == 200
    body2 = r2.json()

    assert body1 != body2, "После истечения TTL registry должен быть пересоздан"
