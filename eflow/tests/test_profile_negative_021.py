import pytest
import uuid

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH = f"/api/v1/employee-profiles/{PROFILE_ID}"

DENY_FIELDS = {
    "cookie", "session", "ip-address", "authenticated", "recovered",
    "internalflags", "stacktrace", "exception", "<html", "backendonly"
}


@pytest.mark.integration
def test_profile_negative_021_strict_stateless_unauthorized(api_client):
    # Выполняем серию запросов без каких-либо средств идентификации
    results = []

    for _ in range(2):
        unique_rid = str(uuid.uuid4())
        # Явно убеждаемся, что в запросе нет ни токена, ни кук
        response = api_client.get(
            PATH,
            headers={"X-Request-ID": unique_rid},
            cookies={}  # Очистка кук, если клиент их хранит
        )
        results.append((response, unique_rid))

    # 1. Проверка первого запроса
    resp1, rid1 = results[0]
    assert resp1.status_code == 401
    assert resp1.headers.get("Content-Type") == "application/json"
    assert "no-store" in resp1.headers.get("Cache-Control", "").lower()
    assert "Authorization" in resp1.headers.get("Vary", "")
    assert "ETag" not in resp1.headers

    data1 = resp1.json()
    assert data1["code"] == "UNAUTHORIZED"
    assert data1["traceId"] == rid1

    # 2. Проверка второго запроса (исключение контекстного восстановления)
    resp2, rid2 = results[1]
    assert resp2.status_code == 401
    data2 = resp2.json()
    assert data2["traceId"] == rid2

    # Структура должна быть идентичной, но traceId обязан быть уникальным
    assert data1["code"] == data2["code"]
    assert data1["traceId"] != data2["traceId"]

    # 3. Security Audit: проверка отсутствия упоминаний механизмов сессий
    for resp, _ in results:
        raw_low = resp.text.lower()
        for field in DENY_FIELDS:
            assert field not in raw_low

        # Проверка отсутствия данных профиля или старых ID
        assert "3fa85f64" not in raw_low
        assert "prid" not in raw_low
        assert "12345" not in raw_low

    # Убеждаемся, что ответ не пришел из кэша
    assert "hit" not in resp2.headers.get("X-Cache", "").lower()