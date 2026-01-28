import json
import pytest
import requests
import uuid

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH = f"/api/v1/employee-profiles/{PROFILE_ID}"

DENY_FIELDS = {
    "people-service", "peopleservice", "upstream", "timeout", "latency",
    "internalflags", "stacktrace", "exception", "<html", "configsource",
    "sql", "select", "connect"
}


@pytest.mark.integration
def test_profile_timeout_012_people_service_latency(mocker, api_client, auth_header):
    trace_id = str(uuid.uuid4())

    # Имитируем ошибку таймаута при обращении к People Service
    # Согласно контракту, возвращаем 504 Gateway Timeout
    error_body = {
        "code": "PEOPLE_SERVICE_TIMEOUT",
        "message": "Information about the employee could not be retrieved in time",
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
        "X-Request-ID": trace_id,
        "Vary": "Authorization"
    }

    # Универсальный патч согласно вашим инструкциям
    mocker.patch.object(requests.Session, "request", return_value=mock_resp)
    mocker.patch("requests.request", return_value=mock_resp)

    response = api_client.get(
        PATH,
        headers={
            **auth_header,
            "X-Request-ID": trace_id
        }
    )

    # 1. Проверка статуса ответа
    assert response.status_code == 504
    assert response.headers.get("Content-Type") == "application/json"

    # 2. Проверка структуры ErrorResponse и корреляции ID
    data = response.json()
    assert data["code"] == "PEOPLE_SERVICE_TIMEOUT"
    assert data["traceId"] == trace_id
    assert data["details"] == []

    # 3. Security Audit: отсутствие технических подробностей и названий сервисов
    raw_low = response.text.lower()
    for field in DENY_FIELDS:
        assert field not in raw_low
        assert field not in [str(k).lower() for k in data.keys()]

    # 4. Проверка заголовков управления кэшем
    assert "no-store" in response.headers.get("Cache-Control", "").lower()

    # Проверка отсутствия старых ID и PII
    assert "prid" not in raw_low
    assert "12345" not in raw_low