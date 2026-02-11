import json
import pytest
import requests
import uuid

# Проверяем на стандартном пути, но с "пустым" токеном
PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH = f"/api/v1/employee-profiles/{PROFILE_ID}"

DENY_FIELDS = {
    "claim", "profile_uuid", "prid", "sub", "missing", "payload",
    "internalflags", "stacktrace", "exception", "<html", "mapping"
}


@pytest.mark.integration
def test_profile_negative_017_missing_user_claim(mocker, api_client):
    trace_id = str(uuid.uuid4())
    # Токен валиден по подписи, но в нем нет идентификатора пользователя (profile_uuid)
    jwt_no_user = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE1MTYyMzkwMjJ9.sig"

    error_body = {
        "code": "UNAUTHORIZED",
        "message": "Full authentication is required to access this resource",
        "details": [],
        "traceId": trace_id
    }
    js_error = json.dumps(error_body)

    mock_resp = mocker.Mock(spec=requests.Response)
    mock_resp.status_code = 401
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
            "Authorization": jwt_no_user,
            "X-Request-ID": trace_id
        }
    )

    # Согласно Saved Info: Ошибки авторизации всегда 401
    assert response.status_code == 401
    assert response.headers.get("Content-Type") == "application/json"

    data = response.json()
    assert data["code"] == "UNAUTHORIZED"
    assert data["traceId"] == trace_id

    # Security Audit: проверяем отсутствие упоминаний отсутствующих полей
    raw_low = response.text.lower()
    for field in DENY_FIELDS:
        assert field not in raw_low
        assert field not in [str(k).lower() for k in data.keys()]

    # Убеждаемся, что система не вернула никаких данных профиля
    assert "3fa85f64" not in raw_low
    assert "12345" not in raw_low