import pytest
import uuid

# Берем два разных UUID: один существующий (другого юзера), второй — случайный
PROFILE_ID_EXISTENT = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PROFILE_ID_RANDOM = str(uuid.uuid4())

DENY_FIELDS = {
    "not found", "exists", "db", "mapping", "null", "none",
    "internalflags", "stacktrace", "exception", "<html", "backendonly"
}


@pytest.mark.integration
def test_profile_negative_032_identical_forbidden_messages(api_client, auth_header):
    responses = []

    # 1. Выполняем запросы к разным профилям
    for target_id in [PROFILE_ID_EXISTENT, PROFILE_ID_RANDOM]:
        path = f"/api/v1/employee-profiles/{target_id}"
        res = api_client.get(path, headers=auth_header)
        responses.append(res)

    res1, res2 = responses[0], responses[1]

    # 2. Проверка статуса (согласно Saved Info: RBAC/Forbidden — 403)
    assert res1.status_code == 403
    assert res2.status_code == 403

    data1 = res1.json()
    data2 = res2.json()

    # 3. Ключевая проверка: Сообщения и коды ошибок должны быть идентичны
    assert data1["code"] == data2["code"]
    assert data1["message"] == data2["message"]
    assert data1["details"] == data2["details"]

    # При этом traceId должны быть уникальными
    assert data1["traceId"] != data2["traceId"]

    # 4. Security Audit на отсутствие утечек в обоих ответах
    for res in responses:
        raw_low = res.text.lower()
        data = res.json()

        # Проверка отсутствия UUID в теле ошибки (маскирование)
        assert PROFILE_ID_EXISTENT.lower() not in raw_low
        assert PROFILE_ID_RANDOM.lower() not in raw_low

        for field in DENY_FIELDS:
            assert field not in raw_low
            assert field not in [str(k).lower() for k in data.keys()]

        # Проверка отсутствия старых идентификаторов
        assert "prid" not in raw_low
        assert "12345" not in raw_low

    # Проверка обязательных заголовков
    assert "no-store" in res1.headers.get("Cache-Control", "").lower()
    assert "Authorization" in res1.headers.get("Vary", "")