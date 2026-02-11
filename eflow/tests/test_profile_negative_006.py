import pytest
import uuid
import base64

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH = f"/api/v1/employee-profiles/{PROFILE_ID}"

DENY_FIELDS = {
    "role", "permission", "policy", "acl", "claim", "scope",
    "internalflags", "internalid", "backendonly", "stacktrace",
    "exception", "<html"
}


@pytest.mark.integration
def test_profile_negative_006_no_acl_leak(api_client, auth_header):
    response = api_client.get(
        PATH,
        headers=auth_header
    )

    assert response.status_code == 403

    data = response.json()
    raw_text = response.text
    raw_low = raw_text.lower()

    # 1. Проверка стандартных полей контракта
    assert data["code"] == "FORBIDDEN"
    assert "traceId" in data

    # 2. Проверка заголовков корреляции
    x_request_id = response.headers.get("X-Request-ID")
    assert x_request_id is not None
    # traceId должен быть связан с X-Request-ID или быть им
    assert data["traceId"] in [x_request_id, f"tr-{x_request_id}"]

    # 3. Рекурсивный аудит всех полей на предмет утечек
    def scan_dictionary(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                assert str(k).lower() not in DENY_FIELDS, f"Leak in key: {k}"
                scan_dictionary(v)
        elif isinstance(obj, list):
            for item in obj:
                scan_dictionary(item)
        elif isinstance(obj, str):
            val_low = obj.lower()
            # Проверка на наличие названий политик или ролей в сообщениях
            for field in DENY_FIELDS:
                assert field not in val_low, f"Leak in value: {obj}"

            # Проверка на наличие base64-строк (похожих на токены или части JWT)
            # Исключаем короткие строки и traceId
            if len(obj) > 30 and "." in obj:
                assert not obj.startswith("ey"), "Found JWT-like string in response"

    scan_dictionary(data)

    # 4. Общий аудит сырого текста
    for field in DENY_FIELDS:
        assert field not in raw_low

    assert "prid" not in raw_low
    assert "12345" not in raw_low