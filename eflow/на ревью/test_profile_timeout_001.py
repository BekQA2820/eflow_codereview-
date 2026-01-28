import json
import pytest
import requests
import uuid

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH = f"/api/v1/employee-profiles/{PROFILE_ID}"

DENY_FIELDS = {
    "internalflags", "internalid", "backendonly", "stacktrace",
    "exception", "<html", "upstream", "connection", "timeout",
    "requiredroles", "requiredpermissions"
}


@pytest.mark.integration
def test_profile_timeout_001_backend_hang(mocker, api_client, auth_header):
    trace_id = str(uuid.uuid4())

    # Имитируем стандартный ответ шлюза при таймауте бэкенда
    error_body = {
        "code": "GATEWAY_TIMEOUT",
        "message": "The upstream server failed to respond in time",
        "details": [],
        "traceId": trace_id
    }
    js_error = json.dumps(error_body)

    # Настройка мока: имитируем либо выброс исключения таймаута,
    # либо возврат 504 от внутреннего прокси
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

    mocker.patch.object(requests.Session, "request", return_value=mock_resp)
    mocker.patch("requests.request", return_value=mock_resp)

    # Выполнение запроса
    response = api_client.get(
        PATH,
        headers=auth_header
    )

    # Проверка статуса (согласноSaved Info: 504 Gateway Timeout)
    assert response.status_code == 504
    assert response.headers.get("Content-Type") == "application/json"
    assert "no-store" in response.headers.get("Cache-Control", "").lower()

    data = response.json()
    assert data["code"] == "GATEWAY_TIMEOUT"
    assert data["traceId"] == trace_id

    # Security Audit: проверка отсутствия технических деталей об апстриме или таймауте
    raw_low = response.text.lower()
    for field in DENY_FIELDS:
        assert field not in raw_low
        assert field not in [str(k).lower() for k in data.keys()]

    # Проверка на отсутствие HTML (частая ошибка Nginx при 504)
    assert "<html" not in raw_low
    assert "prid" not in raw_low
    assert "12345" not in raw_low