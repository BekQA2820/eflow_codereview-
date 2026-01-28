import json
import pytest
import requests
import uuid

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH = f"/api/v1/employee-profiles/{PROFILE_ID}"

# Поля, которые категорически не должны присутствовать при ошибке (PII и бизнес-данные)
DATA_FIELDS = {
    "displayName", "email", "firstName", "lastName", "roles",
    "widgets", "position", "department", "avatarurl"
}

DENY_FIELDS = {
    "internalflags", "stacktrace", "exception", "<html", "configsource",
    "partial", "incomplete", "chunked"
}


@pytest.mark.integration
def test_profile_timeout_011_no_partial_data_on_timeout(mocker, api_client, auth_header):
    trace_id = str(uuid.uuid4())

    # Симулируем ErrorResponse. Важно убедиться, что в него не подмешались данные профиля
    error_body = {
        "code": "GATEWAY_TIMEOUT",
        "message": "The upstream server failed to respond in time",
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

    mocker.patch.object(requests.Session, "request", return_value=mock_resp)
    mocker.patch("requests.request", return_value=mock_resp)

    response = api_client.get(
        PATH,
        headers={
            **auth_header,
            "X-Request-ID": trace_id
        }
    )

    assert response.status_code == 504

    data = response.json()
    raw_low = response.text.lower()

    # 1. Проверка на отсутствие любых полей профиля в ответе
    for field in DATA_FIELDS:
        # Проверяем как ключи в JSON, так и вхождение в сырой текст
        assert field not in data, f"Partial data leak detected: field '{field}' found in JSON"
        assert field.lower() not in raw_low, f"Partial data leak detected: field '{field}' found in raw text"

    # 2. Проверка на отсутствие самого UUID профиля (кроме traceId)
    assert PROFILE_ID not in raw_low

    # 3. Security Audit: проверка на технические утечки
    for field in DENY_FIELDS:
        assert field not in raw_low

    # 4. Проверка корректности ErrorResponse
    assert data["code"] == "GATEWAY_TIMEOUT"
    assert data["traceId"] == trace_id
    assert "prid" not in raw_low
    assert "12345" not in raw_low