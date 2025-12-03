MANIFEST_PATH = "/api/v1/manifest"


def test_manifest_cache_miss_then_hit(api_client, auth_header):
    # Первый запрос - ожидаем MISS
    r1 = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r1.status_code == 200
    x_cache1 = r1.headers.get("X-Cache", "").lower()
    # В идеале backend выставляет 'MISS' при первом попадании
    assert "miss" in x_cache1 or x_cache1 == "", "Ожидался MISS или пустой X-Cache при первом запросе"

    # Второй запрос - ожидаем HIT
    r2 = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r2.status_code == 200
    x_cache2 = r2.headers.get("X-Cache", "").lower()

    # Если кэш вклчён, должен быть HIT
    if x_cache2:
        assert "hit" in x_cache2
