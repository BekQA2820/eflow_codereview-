import pytest
import uuid

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH = f"/api/v1/employee-profiles/{PROFILE_ID}"

DENY_FIELDS = {
    "internalflags", "stacktrace", "exception", "<html", "configsource",
    "rbac", "permission", "logic", "check", "bypass", "injection"
}


@pytest.mark.integration
def test_profile_negative_030_ignore_pseudo_auth_headers(api_client):
    unique_rid = str(uuid.uuid4())
    fake_roles = "Admin,Manager,SuperUser"
    fake_hash = "8ba2f99547d25e0c800843236e76554b"

    # Отправляем запрос с "поддельными" правами в кастомных заголовках,
    # но без заголовка Authorization
    response = api_client.get(
        PATH,
        headers={
            "X-Roles": fake_roles,
            "X-Roles-Hash": fake_hash,
            "X-Request-ID": unique_rid
        }
    )

    # 1. Проверка статуса и базовых заголовков
    assert response.status_code == 401
    assert response.headers.get("Content-Type") == "application/json"
    assert "no-store" in response.headers.get("Cache-Control", "").lower()
    assert "Authorization" in response.headers.get("Vary", "")
    assert "ETag" not in response.headers

    # 2. Проверка структуры ErrorResponse
    data = response.json()
    assert data["code"] == "UNAUTHORIZED"
    assert "message" in data
    assert isinstance(data.get("details"), list)
    assert data["traceId"] == unique_rid

    # 3. Security Audit: проверка отсутствия влияния переданных фейковых данных
    raw_low = response.text.lower()

    # Система не должна "отзеркаливать" наши фейковые роли или хеш в сообщении об ошибке
    assert "admin" not in raw_low
    assert fake_hash not in raw_low

    for field in DENY_FIELDS:
        assert field not in raw_low
        assert field not in [str(k).lower() for k in data.keys()]

    # Проверка отсутствия старых ID и утечек PII
    assert "prid" not in raw_low
    assert "12345" not in raw_low
    assert "3fa85f64" not in raw_low