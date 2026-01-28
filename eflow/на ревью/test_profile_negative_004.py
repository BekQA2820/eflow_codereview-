import pytest
import uuid
import re

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH = f"/api/v1/employee-profiles/{PROFILE_ID}"

DENY_FIELDS = {
    "internalflags", "internalid", "backendonly", "stacktrace",
    "exception", "<html", "requiredroles", "requiredpermissions",
    "email", "phone", "first_name", "last_name"
}


@pytest.mark.integration
def test_profile_negative_004_forbidden_roles(api_client, auth_header):
    # Используем валидный токен (auth_header), но имитируем отсутствие прав на уровне RBAC
    # В реальной системе это достигается использованием токена "обычного" пользователя
    # при попытке доступа к защищенному ресурсу или чужому профилю.

    response = api_client.get(
        PATH,
        headers=auth_header
    )

    # Согласно Saved Info: 403 используется для RBAC issues
    assert response.status_code == 403
    assert response.headers.get("Content-Type") == "application/json"
    assert "no-store" in response.headers.get("Cache-Control", "").lower()

    # Проверка заголовков Vary и X-Roles-Hash
    vary = response.headers.get("Vary", "")
    assert "Authorization" in vary
    assert "X-Roles-Hash" in vary

    roles_hash = response.headers.get("X-Roles-Hash", "")
    assert re.fullmatch(r"[a-f0-9]{32}", roles_hash.lower()) is not None

    data = response.json()
    assert data["code"] == "FORBIDDEN"
    assert "traceId" in data
    assert "message" in data

    raw_low = response.text.lower()
    # Проверка на отсутствие PII и технических полей (Security Audit)
    for field in DENY_FIELDS:
        assert field not in raw_low
        assert field not in [str(k).lower() for k in data.keys()]

    # Проверка на отсутствие утечки существования ресурса через детали
    assert PROFILE_ID not in data.get("message", "")

    assert "prid" not in raw_low
    assert "12345" not in raw_low