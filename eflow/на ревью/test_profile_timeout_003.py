import json
import pytest
import requests
import uuid

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH = f"/api/v1/employee-profiles/{PROFILE_ID}"

DENY_FIELDS = {
    "internalflags", "stacktrace", "exception", "<html",
    "backendonly", "debuginfo"
}


@pytest.mark.integration
def test_profile_timeout_003_no_etag_on_error(mocker, api_client, auth_header):
    trace_id = str(uuid.uuid4())

    # 1. Сценарий: Успешный запрос (для фиксации того, как выглядит ETag в норме)
    success_body = {"id": PROFILE_ID, "status": "active"}
    mock_success = mocker.Mock(spec=requests.Response)
    mock_success.status_code = 200
    mock_success.json.return_value = success_body
    mock_success.text = json.dumps(success_body)
    mock_success.content = mock_success.text.encode("utf-8")
    mock_success.headers = {
        "Content-Type": "application/json",
        "ETag": 'W/"33a64df551425fcc55e4d42a148795d9f25f89d4"',
        "Cache-Control": "max-age=3600",
        "X-Request-ID": str(uuid.uuid4())
    }

    # 2. Сценарий: Таймаут (ошибочный ответ)
    error_body = {
        "code": "GATEWAY_TIMEOUT",
        "message": "Backend did not respond",
        "traceId": trace_id
    }
    mock_error = mocker.Mock(spec=requests.Response)
    mock_error.status_code = 504
    mock_error.json.return_value = error_body
    mock_error.text = json.dumps(error_body)
    mock_error.content = mock_error.text.encode("utf-8")
    mock_error.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization, X-Roles-Hash",
        "X-Request-ID": trace_id
    }

    # Патчим последовательность ответов
    mocker.patch.object(requests.Session, "request", side_effect=[mock_success, mock_error])
    mocker.patch("requests.request", side_effect=[mock_success, mock_error])

    # Исполнение первого (успешного) запроса
    r1 = api_client.get(PATH, headers=auth_header)
    assert r1.status_code == 200
    assert "ETag" in r1.headers

    # Исполнение второго (неудачного) запроса
    r2 = api_client.get(PATH, headers=auth_header)

    # Критическая проверка: ошибки не должны кэшироваться через ETag
    assert r2.status_code == 504
    assert "ETag" not in r2.headers
    assert "no-store" in r2.headers.get("Cache-Control", "").lower()

    vary = r2.headers.get("Vary", "")
    assert "Authorization" in vary
    assert "X-Roles-Hash" in vary

    # Security Audit
    data = r2.json()
    raw_low = r2.text.lower()
    for field in DENY_FIELDS:
        assert field not in raw_low
        assert field not in [str(k).lower() for k in data.keys()]

    assert "prid" not in raw_low
    assert "12345" not in raw_low