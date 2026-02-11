import pytest
import uuid
import time

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH = f"/api/v1/employee-profiles/{PROFILE_ID}"


@pytest.mark.integration
def test_profile_timeout_009_no_cache_on_timeout(api_client, auth_header):
    # Выполняем серию запросов в условиях нестабильного бэкенда
    responses = []

    for _ in range(2):
        unique_rid = str(uuid.uuid4())
        # Имитируем запрос. В реальности здесь бэкенд должен вернуть 504
        response = api_client.get(
            PATH,
            headers={
                **auth_header,
                "X-Request-ID": unique_rid
            }
        )
        responses.append((response, unique_rid))
        # Небольшая пауза между запросами для проверки срабатывания TTL кэша (если бы он был)
        time.sleep(0.1)

    # 1. Анализ первого ответа
    resp1, rid1 = responses[0]
    assert resp1.status_code == 504
    assert "no-store" in resp1.headers.get("Cache-Control", "").lower()
    assert "ETag" not in resp1.headers
    assert resp1.json()["traceId"] == rid1

    # 2. Анализ второго ответа (проверка отсутствия кэширования)
    resp2, rid2 = responses[1]
    assert resp2.status_code == 504

    # Заголовок X-Cache (если есть) не должен быть HIT
    x_cache = resp2.headers.get("X-Cache", "").lower()
    assert "hit" not in x_cache

    # Ключевая проверка: traceId должен обновиться, что доказывает проход запроса мимо кэша
    data2 = resp2.json()
    assert data2["traceId"] == rid2
    assert data2["traceId"] != rid1

    # 3. Security Audit: отсутствие утечек
    raw_low = resp2.text.lower()
    assert "stacktrace" not in raw_low
    assert "3fa85f64" not in raw_low
    assert "prid" not in raw_low