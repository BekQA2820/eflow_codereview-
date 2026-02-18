import json
import pytest
import requests
import uuid

PROFILE_ID_A = "3fa85f64-5717-4562-b3fc-aaaaaaaaaaaa"
PROFILE_ID_B = "3fa85f64-5717-4562-b3fc-bbbbbbbbbbbb"

PATH_A = f"/employee-profiles/{PROFILE_ID_A}"
PATH_B = f"/employee-profiles/{PROFILE_ID_B}"

DENY_FIELDS = {
    "internalflags", "internalid", "requiredpermissions", "configsource",
    "internalmeta", "stacktrace", "exception", "<html", "debuginfo"
}


@pytest.mark.integration
def test_rbac_profile_049_user_data_isolation_same_roles(api_client):
    body_a = {"profile_id": PROFILE_ID_A, "displayName": "User A", "email": "a@example.com"}
    body_b = {"profile_id": PROFILE_ID_B, "displayName": "User B", "email": "b@example.com"}

    headers_a = {"Authorization": "Bearer A"}
    headers_b = {"Authorization": "Bearer B"}

    
    r_a1 = api_client.get(PATH_A, headers=headers_a)
    r_a2 = api_client.get(PATH_A, headers=headers_a)
    r_b = api_client.get(PATH_B, headers=headers_b)

    # Проверка статусов
    assert r_a1.status_code == 200
    assert r_a2.status_code == 200
    assert r_b.status_code == 200

    data_a = r_a1.json()
    data_b = r_b.json()

    # Проверка различия в email
    assert data_a["profile_id"] == PROFILE_ID_A
    assert data_b["profile_id"] == PROFILE_ID_B
    assert data_a["email"] != data_b["email"]

    # Проверка кэша
    assert r_a1.headers.get("X-Cache") != r_b.headers.get("X-Cache")

    # Security Audit: отсутствие утечек данных
    for r in (r_a1, r_b):
        raw_low = r.text.lower()
        clean_text = raw_low.replace(PROFILE_ID_A, "").replace(PROFILE_ID_B, "")

        for tech_token in DENY_FIELDS:
            assert tech_token not in clean_text, f"Security Leak: found '{tech_token}'"

        for rbac_token in ["roles", "permissions", "scopes"]:
            assert rbac_token not in raw_low

    # Кросс-проверка отсутствия данных другого профиля
    assert "user a" not in r_b.text.lower()
    assert "a@example.com" not in r_b.text.lower()

    # Проверка отсутствия старых ID и PII (Saved Info)
    assert "prid" not in r_a1.text.lower()
    assert "12345" not in r_a1.text.lower()
