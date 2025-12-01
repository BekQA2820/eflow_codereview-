def test_s3_timeout_fallback(api_client, auth_header, simulate_s3_timeout):
    """
    Проверка устойчивости:
     S3 зависает - сервс должен вернуть старый кэшированный манифест
    """

    # 1. Получаем актуальный манифест
    first = api_client.get("/api/v1/manifest", headers=auth_header)
    assert first.status_code == 200
    cached_manifest = first.json()

    # 2. Симулируем задержку/таймаут
    simulate_s3_timeout()

    # 3. Запрос должен пройти, но через fallback
    resp = api_client.get("/api/v1/manifest", headers=auth_header)
    assert resp.status_code == 200

    # Данные должны совпадать со старой версией
    assert resp.json() == cached_manifest
