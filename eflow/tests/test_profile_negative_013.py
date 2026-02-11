import pytest

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH = f"/api/v1/employee-profiles/{PROFILE_ID}"

DENY_FIELDS = {
    "parse", "split", "indexoutofrange", "invalid_header", "prefix",
    "internalflags", "stacktrace", "exception", "<html", "bearer"
}


@pytest.mark.integration
@pytest.mark.parametrize("invalid_header", [
    "Basic dXNlcjpwYXNz",  # Неверный тип схемы
    "Bearer",  # Отсутствует сам токен
    "eyJhGciOiJIUzI1NiJ9...",  # Отсутствует префикс Bearer
    "Bearer  extra_space_token",  # Двойной пробел
    "Token 12345",  # Несуществующая схема
    ""  # Пустой заголовок
])
def test_profile_negative_013_malformed_auth_header(api_client, invalid_header):
    response = api_client.get(
        PATH,
        headers={"Authorization": invalid_header}
    )

    # Согласно Saved Info: Любая ошибка авторизации/токена — это 401
    assert response.status_code == 401
    assert response.headers.get("Content-Type") == "application/json"
    assert "no-store" in response.headers.get("Cache-Control", "").lower()

    data = response.json()
    assert data["code"] == "UNAUTHORIZED"
    assert "message" in data
    assert "traceId" in data

    raw_low = response.text.lower()
    # Проверяем, что в сообщении нет деталей о том, что именно не так с форматом
    for field in DENY_FIELDS:
        # Исключаем 'bearer' из проверки, если мы сами его послали в заголовке запроса
        # (в ответе его быть не должно)
        assert field not in raw_low
        assert field not in [str(k).lower() for k in data.keys()]

    assert "prid" not in raw_low
    assert "12345" not in raw_low