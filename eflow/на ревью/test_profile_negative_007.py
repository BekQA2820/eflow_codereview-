import pytest
import uuid

PATH = "/api/v1/employee-profiles/3fa85f64-5717-4562-b3fc-2c963f66afa6"

DENY_FIELDS = {
    "internalflags", "stacktrace", "exception", "<html",
    "x-cache", "hit", "backendonly", "debuginfo"
}


@pytest.mark.integration
def test_profile_negative_007_no_cache_on_401(api_client):
    # 1. Первый запрос без Authorization
    trace_id_1 = str(uuid.uuid4())
    headers_1 = {"X-Request-ID": trace_id_1}

    r1 = api_client.get(PATH, headers=headers_1)

    assert r1.status_code == 401
    assert r1.headers.get("Content-Type") == "application/json"
    assert "no-store" in r1.headers.get("Cache-Control", "").lower()
    assert "Authorization" in r1.headers.get("Vary", "")
    assert "ETag" not in r1.headers

    data1 = r1.json()
    assert data1["code"] == "UNAUTHORIZED"
    rid1 = r1.headers.get("X-Request-ID")

    # 2. Второй запрос без Authorization с другим Request-ID
    trace_id_2 = str(uuid.uuid4())
    headers_2 = {"X-Request-ID": trace_id_2}

    r2 = api_client.get(PATH, headers=headers_2)

    assert r2.status_code == 401
    data2 = r2.json()
    rid2 = r2.headers.get("X-Request-ID")

    # 3. Проверка отсутствия кэширования и изоляции
    # traceId в теле и X-Request-ID в заголовках должны быть уникальными для каждого вызова
    assert data1["traceId"] != data2["traceId"]
    assert rid1 != rid2

    # Убеждаемся, что второй запрос не помечен как HIT из кэша
    x_cache = r2.headers.get("X-Cache", "").lower()
    assert "hit" not in x_cache

    # 4. Security Audit
    for resp in [r1, r2]:
        raw_low = resp.text.lower()
        for field in DENY_FIELDS:
            # Исключаем 'hit' из проверки заголовков, если он там может быть как MISS
            if field == "hit" and "x-cache" in resp.headers:
                assert resp.headers.get("X-Cache", "").lower() != "hit"
                continue
            assert field not in raw_low

        # Проверка на отсутствие данных профиля в ответе ошибки
        assert "profile_id" not in raw_low
        assert "version" not in raw_low
        assert "prid" not in raw_low
        assert "12345" not in raw_low