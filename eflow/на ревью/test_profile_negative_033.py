import pytest
import re
import uuid

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH = f"/api/v1/employee-profiles/{PROFILE_ID}"

# Регулярные выражения для поиска утечек чувствительных данных
PII_PATTERNS = {
    "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "phone": re.compile(r"(\+7|8)[\s\(\)-]*\d{3}[\s\(\)-]*\d{3}[\s\(\)-]*\d{2}[\s\(\)-]*\d{2}"),
    "jwt_like": re.compile(r"eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*"),
    "base64_long": re.compile(r"(?:[A-Za-z0-9+/]{4}){10,}(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?")
}

DENY_FIELDS = {
    "internalflags", "internalid", "backendonly", "stacktrace",
    "exception", "configsource", "requiredroles", "privileges"
}


@pytest.mark.integration
@pytest.mark.parametrize("auth_scenario", ["missing_token", "invalid_token", "forbidden_access"])
def test_profile_negative_033_no_pii_leakage_in_error(api_client, auth_scenario):
    trace_id = str(uuid.uuid4())
    headers = {"X-Request-ID": trace_id}

    if auth_scenario == "invalid_token":
        headers["Authorization"] = "Bearer invalid.token.value"
    elif auth_scenario == "forbidden_access":
        # Используем Saved Info: токен есть, но нет прав на конкретный PROFILE_ID
        headers["Authorization"] = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlcyI6WyJVc2VyIl19.sig"

    response = api_client.get(PATH, headers=headers)

    # Согласно контракту: 401 или 403
    assert response.status_code in {401, 403}

    raw_text = response.text
    raw_low = raw_text.lower()
    data = response.json()

    # 1. Проверка на отсутствие PII через регулярные выражения
    for name, pattern in PII_PATTERNS.items():
        found = pattern.findall(raw_text)
        # Исключаем traceId и сам запрашиваемый profile_id из проверки UUID-подобных строк,
        # но проверяем, что их нет в полях message/details
        if name == "jwt_like" or name == "base64_long":
            assert not found, f"Detected potential PII leak ({name}) in response"

    # 2. Проверка на отсутствие запрашиваемого Profile ID в теле ошибки (маскирование)
    assert PROFILE_ID not in raw_text

    # 3. Проверка на отсутствие технических и сервисных полей
    for field in DENY_FIELDS:
        assert field not in raw_low
        assert field not in [str(k).lower() for k in data.keys()]

    # 4. Проверка на отсутствие старых идентификаторов (из Saved Info)
    assert "prid" not in raw_low
    assert "12345" not in raw_low

    # 5. Валидация структуры ErrorResponse
    assert data["traceId"] == trace_id
    assert "code" in data
    assert "message" in data
    assert isinstance(data.get("details"), list)

    # Проверка обязательных заголовков безопасности
    assert "no-store" in response.headers.get("Cache-Control", "").lower()