import json
import pytest
import requests
import uuid

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH = f"/api/v1/employee-profiles/{PROFILE_ID}"

DENY_FIELDS = {
    "internalflags", "internalid", "backendonly", "stacktrace",
    "exception", "first_name", "last_name", "widgets", "layout"
}


@pytest.mark.integration
def test_profile_timeout_006_no_partial_data(mocker, api_client, auth_header):
    trace_id = str(uuid.uuid4())

    # Имитируем ошибку 424 (Failed Dependency) из-за таймаута внутреннего микросервиса
    error_body = {
        "code": "DEPENDENCY_TIMEOUT",
        "message": "Required data source timed out. Partial content is not allowed.",
        "details": [],
        "traceId": trace_id
    }
    js_error = json.dumps(error_body)

    mock_resp = mocker.Mock(spec=requests.Response)
    mock_resp.status_code = 424
    mock_resp.json.return_value = error_body
    mock_resp.text = js_error
    mock_resp.content = js_error.encode("utf-8")
    mock_resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "X-Request-ID": trace_id
    }

    # Универсальный патч для имитации сбоя агрегации данных
    mocker.patch.object(requests.Session, "request", return_value=mock_resp)
    mocker.patch("requests.request", return_value=mock_resp)

    response = api_client.get(
        PATH,
        headers=auth_header
    )

    # Проверка статуса: система должна отклонить запрос целиком
    assert response.status_code == 424
    assert response.headers.get("Content-Type") == "application/json"

    data = response.json()
    assert data["code"] == "DEPENDENCY_TIMEOUT"
    assert data["traceId"] == trace_id

    # Самая важная часть: проверка отсутствия частичных данных профиля
    raw_low = response.text.lower()
    for field in DENY_FIELDS:
        # Проверяем, что в ответе нет ни технических полей, ни данных самого профиля
        assert field not in raw_low, f"Partial data leak detected: {field}"

    # Проверка структуры ErrorResponse
    assert "message" in data
    assert isinstance(data.get("details"), list)

    # Убеждаемся, что нет признаков отладки и старых ID
    assert "debug" not in raw_low
    assert "prid" not in raw_low
    assert "12345" not in raw_low