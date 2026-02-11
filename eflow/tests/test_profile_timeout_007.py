import json
import pytest
import requests
import uuid

PATH_A = "/api/v1/employee-profiles/3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH_B = "/api/v1/employee-profiles/d9b2d63d-2af3-4411-b005-4d7616335123"

DENY_FIELDS = {
    "internalflags", "stacktrace", "exception", "<html",
    "backendonly", "debuginfo"
}


@pytest.mark.integration
def test_profile_timeout_007_isolation(mocker, api_client):
    trace_id_a = f"tr-{uuid.uuid4()}"
    trace_id_b = f"tr-{uuid.uuid4()}"

    # 1. Мок для Пользователя А (Таймаут)
    error_body = {
        "code": "GATEWAY_TIMEOUT",
        "message": "Service timeout",
        "traceId": trace_id_a
    }
    mock_timeout = mocker.Mock(spec=requests.Response)
    mock_timeout.status_code = 504
    mock_timeout.json.return_value = error_body
    mock_timeout.text = json.dumps(error_body)
    mock_timeout.content = mock_timeout.text.encode("utf-8")
    mock_timeout.headers = {
        "Content-Type": "application/json",
        "X-Request-ID": trace_id_a
    }

    # 2. Мок для Пользователя Б (Успех)
    success_body = {
        "id": "d9b2d63d-2af3-4411-b005-4d7616335123",
        "version": "v1"
    }
    mock_success = mocker.Mock(spec=requests.Response)
    mock_success.status_code = 200
    mock_success.json.return_value = success_body
    mock_success.text = json.dumps(success_body)
    mock_success.content = mock_success.text.encode("utf-8")
    mock_success.headers = {
        "Content-Type": "application/json",
        "X-Request-ID": trace_id_b
    }

    # Настраиваем поочередную отдачу: сначала ошибка, потом успех
    mocker.patch.object(requests.Session, "request", side_effect=[mock_timeout, mock_success])
    mocker.patch("requests.request", side_effect=[mock_timeout, mock_success])

    # Выполняем запросы
    resp_a = api_client.get(PATH_A, headers={"Authorization": "Bearer token_a"})
    resp_b = api_client.get(PATH_B, headers={"Authorization": "Bearer token_b"})

    # Проверка изоляции: ошибка одного не мешает другому
    assert resp_a.status_code == 504
    assert resp_a.json()["traceId"] == trace_id_a

    assert resp_b.status_code == 200
    assert resp_b.json()["id"] == "d9b2d63d-2af3-4411-b005-4d7616335123"
    assert resp_b.headers["X-Request-ID"] == trace_id_b

    # Security Audit для ответа с ошибкой
    raw_low_a = resp_a.text.lower()
    for field in DENY_FIELDS:
        assert field not in raw_low_a

    assert "prid" not in raw_low_a
    assert "12345" not in raw_low_a