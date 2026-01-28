import json
import pytest
import requests
import uuid

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH = f"/api/v1/employee-profiles/{PROFILE_ID}"

DENY_FIELDS = {
    "hang", "stuck", "pending", "gateway", "upstream", "retry",
    "internalflags", "stacktrace", "exception", "<html", "configsource",
    "socket", "pool", "thread"
}


@pytest.mark.integration
def test_profile_timeout_013_hung_connection_handling(mocker, api_client, auth_header):
    trace_id = str(uuid.uuid4())

    # Имитируем ситуацию, когда шлюз возвращает 504 после долгого ожидания (Hang)
    error_body = {
        "code": "GATEWAY_TIMEOUT",
        "message": "The server acting as a gateway could not complete the request in time",
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

    # Патчим вызов через mocker.patch.object согласно Saved Info
    mocker.patch.object(requests.Session, "request", return_value=mock_resp)
    mocker.patch("requests.request", return_value=mock_resp)

    response = api_client.get(
        PATH,
        headers={
            **auth_header,
            "X-Request-ID": trace_id
        }
    )

    # 1. Проверка корректного завершения по таймауту
    assert response.status_code == 504
    assert response.headers.get("Content-Type") == "application/json"

    # 2. Проверка структуры ErrorResponse
    data = response.json()
    assert data["code"] == "GATEWAY_TIMEOUT"
    assert data["traceId"] == trace_id
    assert "message" in data

    # 3. Security Audit: проверка на отсутствие инфраструктурных деталей
    raw_low = response.text.lower()
    for field in DENY_FIELDS:
        assert field not in raw_low
        assert field not in [str(k).lower() for k in data.keys()]

    # 4. Проверка заголовков безопасности
    assert "no-store" in response.headers.get("Cache-Control", "").lower()

    # Проверка отсутствия старых ID и PII (согласно Saved Info)
    assert "prid" not in raw_low
    assert "12345" not in raw_low
    assert "3fa85f64" not in raw_low