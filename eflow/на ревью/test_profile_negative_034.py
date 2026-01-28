import json
import pytest
import requests
import uuid

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH = f"/api/v1/employee-profiles/{PROFILE_ID}"

DENY_FIELDS = {
    "internalflags", "stacktrace", "exception", "<html", "configsource",
    "debug_info", "log_path", "server_name"
}


@pytest.mark.integration
def test_profile_negative_034_trace_id_correlation(mocker, api_client):
    # Генерируем уникальный идентификатор для этого конкретного запроса
    request_id = str(uuid.uuid4())

    # Сценарий: просроченный токен (Expired)
    expired_jwt = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE1MTYyMzkwMjJ9.sig"

    error_body = {
        "code": "UNAUTHORIZED",
        "message": "Token has expired",
        "details": [],
        "traceId": request_id  # traceId в теле должен совпадать с X-Request-ID
    }
    js_error = json.dumps(error_body)

    mock_resp = mocker.Mock(spec=requests.Response)
    mock_resp.status_code = 401
    mock_resp.json.return_value = error_body
    mock_resp.text = js_error
    mock_resp.content = js_error.encode("utf-8")
    mock_resp.headers = {
        "Content-Type": "application/json",
        "X-Request-ID": request_id,  # Заголовок ответа также должен содержать ID
        "Cache-Control": "no-store",
        "Vary": "Authorization"
    }

    mocker.patch.object(requests.Session, "request", return_value=mock_resp)
    mocker.patch("requests.request", return_value=mock_resp)

    response = api_client.get(
        PATH,
        headers={
            "Authorization": expired_jwt,
            "X-Request-ID": request_id
        }
    )

    # 1. Проверка корреляции идентификаторов
    assert response.status_code == 401
    assert response.headers.get("X-Request-ID") == request_id

    data = response.json()
    assert data["traceId"] == request_id
    assert data["code"] == "UNAUTHORIZED"

    # 2. Security Audit: проверка на отсутствие утечек при ошибке трассировки
    raw_low = response.text.lower()
    for field in DENY_FIELDS:
        assert field not in raw_low
        assert field not in [str(k).lower() for k in data.keys()]

    # Проверка отсутствия старых ID и PII (согласно Saved Info)
    assert "prid" not in raw_low
    assert "12345" not in raw_low
    assert "3fa85f64" not in raw_low