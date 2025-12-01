import time

MANIFEST = "/api/v1/manifest"


def test_rate_limit_recovery(api_client, auth_header):
    r = None

    # Превышаем лимит — должны получить 429
    for _ in range(61):
        r = api_client.get(MANIFEST, headers=auth_header)

    assert r is not None, "Не удалось выполнить ни один запрос"
    assert r.status_code == 429

    retry_after = int(r.headers.get("Retry-After", "1"))

    # Ждём восстановления
    time.sleep(retry_after + 1)

    r2 = api_client.get(MANIFEST, headers=auth_header)

    assert r2.status_code == 200
    assert int(r2.headers.get("X-RateLimit-Remaining", "1")) > 0
