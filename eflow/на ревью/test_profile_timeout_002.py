import json
import pytest
import requests
import uuid

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH = f"/api/v1/employee-profiles/{PROFILE_ID}"

DENY_FIELDS = {
    "http", "https", "s3", "api.external", "sap", "connection refused",
    "internalflags", "stacktrace", "exception", "<html", "backendonly"
}


@pytest.mark.integration
def test_profile_timeout_002_external_api_failure(mocker, api_client, auth_header):
    trace_id = str(uuid.uuid4())

    # Имитируем ответ 424 Failed Dependency согласно контракту
    error_body = {
        "code": "DEPENDENCY_FAILURE",
        "message": "Information temporarily unavailable from external source",
        "details": [],
        "traceId": trace_id
    }
    js_error = json.dumps(error_body)

    # Настройка мока: имитируем ошибку коммуникации с внешним источником
    mock_resp = mocker.Mock(spec=requests.Response)
    mock_resp.status_code = 424
    mock_resp.json.return_value = error_body
    mock_resp.text = js_error
    mock_resp.content = js_error.encode("utf-8")
    mock_resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "X-Request-ID": trace_id
    }

    mocker.patch.object(requests.Session, "request", return_value=mock_resp)
    mocker.patch("requests.request", return_value=mock_resp)

    # Выполнение запроса
    response = api_client.get(
        PATH,
        headers=auth_header
    )

    # Проверка статуса (424 Failed Dependency)
    assert response.status_code == 424
    assert response.headers.get("Content-Type") == "application/json"
    assert "no-store" in response.headers.get("Cache-Control", "").lower()
    assert "Authorization" in response.headers.get("Vary", "")

    data = response.json()
    assert data["code"] == "DEPENDENCY_FAILURE"
    assert data["traceId"] == trace_id
    assert isinstance(data.get("details"), list)

    # Security Audit: проверка на отсутствие URL и имен внешних систем
    raw_low = response.text.lower()
    for field in DENY_FIELDS:
        assert field not in raw_low
        # Проверяем также ключи и значения в JSON объекте
        if isinstance(data.get("message"), str):
            assert field not in data["message"].lower()

    # Убеждаемся, что нет признаков отладки
    assert "debug" not in raw_low
    assert "stacktrace" not in raw_low
    assert "prid" not in raw_low
    assert "12345" not in raw_low