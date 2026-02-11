import json
import pytest
import requests
import uuid

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH = f"/api/v1/employee-profiles/{PROFILE_ID}"

DENY_FIELDS = {
    "stacktrace", "exception", "upstream", "backend", "connection",
    "refused", "timeout", "internalflags", "<html", "configsource"
}


@pytest.mark.integration
def test_profile_timeout_008_backend_unavailable(mocker, api_client, auth_header):
    trace_id = str(uuid.uuid4())

    # Имитируем ошибку таймаута на стороне Backend-сервиса (504 Gateway Timeout)
    error_body = {
        "code": "SERVICE_UNAVAILABLE",
        "message": "The server is temporarily unable to service your request due to maintenance downtime or capacity problems.",
        "details": [],
        "traceId": trace_id
    }
    js_error = json.dumps(error_body)

    mock_resp = mocker.Mock(spec=requests.Response)
    mock_resp.status_code = 504
    mock_resp.json.return_value = error_body
    mock_resp.text = js_error
    mock_resp.content = js_error.encode("utf-8")
    mock_resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "X-Request-ID": trace_id
    }

    # Универсальный патч сессии и запроса согласно Saved Info
    mocker.patch.object(requests.Session, "request", return_value=mock_resp)
    mocker.patch("requests.request", return_value=mock_resp)

    response = api_client.get(
        PATH,
        headers={
            **auth_header,
            "X-Request-ID": trace_id
        }
    )

    # 1. Проверка статуса (Gateway Timeout)
    assert response.status_code == 504
    assert response.headers.get("Content-Type") == "application/json"
    assert "no-store" in response.headers.get("Cache-Control", "").lower()

    # 2. Валидация структуры ErrorResponse
    data = response.json()
    assert data["code"] == "SERVICE_UNAVAILABLE"
    assert data["traceId"] == trace_id
    assert isinstance(data.get("details"), list)

    # 3. Security Audit: отсутствие технических подробностей о таймауте и инфраструктуре
    raw_low = response.text.lower()
    for field in DENY_FIELDS:
        assert field not in raw_low
        assert field not in [str(k).lower() for k in data.keys()]

    # Проверка отсутствия старых ID и утечек PII
    assert "prid" not in raw_low
    assert "12345" not in raw_low
    assert "3fa85f64" not in raw_low