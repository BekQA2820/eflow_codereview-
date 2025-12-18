import json
import pytest

MANIFEST_PATH = "/api/v1/manifest-non-existent"

DENY_FIELDS = {
    "internalFlags",
    "internalId",
    "serviceRouting",
    "debugInfo",
    "backendOnly",
    "requiredPermissions",
    "internalMeta",
    "configSource",
}


def test_error_response_404_not_found(mocker, api_client, auth_header):
    """
    API SEC 005
    Проверка единого ErrorResponse для 404 Not Found
    """


    # 1. Подготавливаем mock ответа

    body = {
        "code": "NOT_FOUND",
        "message": "Resource not found",
        "details": [],
        "traceId": "trace-404-abc",
    }

    response = mocker.Mock()
    response.status_code = 404
    response.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "X-Request-ID": "trace-404-abc",
    }
    response.json.return_value = body
    response.text = json.dumps(body)

    mocker.patch("requests.get", return_value=response)


    # 2. Выполняем запрос

    r = api_client.get(MANIFEST_PATH, headers=auth_header)


    # 3. HTTP-уровень

    assert r.status_code == 404, f"Ожидали 404, получили {r.status_code}"

    ctype = r.headers.get("Content-Type", "")
    assert ctype.startswith("application/json"), f"Некорректный Content-Type: {ctype}"

    cache_control = r.headers.get("Cache-Control", "")
    assert "public" not in cache_control
    assert "max-age" not in cache_control


    # 4. Тело ответа

    data = r.json()
    assert isinstance(data, dict)

    for key in ("code", "message", "details", "traceId"):
        assert key in data, f"Отсутствует обязательное поле '{key}'"

    assert data["code"] == "NOT_FOUND"
    assert isinstance(data["message"], str)
    assert isinstance(data["details"], list)
    assert isinstance(data["traceId"], str)


    # 5. traceId ↔ X-Request-ID

    assert data["traceId"] == r.headers.get("X-Request-ID")


    # 6. Безопасность

    raw = r.text.lower()
    assert "<html" not in raw
    assert "stacktrace" not in raw
    assert "exception" not in raw

    for forbidden in DENY_FIELDS:
        assert forbidden not in raw, f"Найдено запрещённое поле: {forbidden}"
