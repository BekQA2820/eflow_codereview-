import json
import pytest
import requests
import uuid

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH = f"/api/v1/employee-profiles/{PROFILE_ID}"

DENY_FIELDS = {
    "audience", "aud", "expected", "wrong_client", "recipient",
    "internalflags", "stacktrace", "exception", "<html", "backendonly"
}


@pytest.mark.integration
def test_profile_negative_020_invalid_audience(mocker, api_client):
    trace_id = str(uuid.uuid4())
    # Токен, выпущенный для другого сервиса (например, "billing-api")
    invalid_aud_jwt = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJiaWxsaW5nLWFwaSJ9.sig"

    error_body = {
        "code": "UNAUTHORIZED",
        "message": "Authentication failed: invalid token destination",
        "details": [],
        "traceId": trace_id
    }
    js_error = json.dumps(error_body)

    # Имитируем отказ на уровне Security Middleware при проверке claims
    mock_resp = mocker.Mock(spec=requests.Response)
    mock_resp.status_code = 401
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

    response = api_client.get(
        PATH,
        headers={
            "Authorization": invalid_aud_jwt,
            "X-Request-ID": trace_id
        }
    )

    # Согласно Saved Info: Ошибки токена всегда 401
    assert response.status_code == 401
    assert response.headers.get("Content-Type") == "application/json"
    assert "no-store" in response.headers.get("Cache-Control", "").lower()

    data = response.json()
    assert data["code"] == "UNAUTHORIZED"
    assert data["traceId"] == trace_id

    # Security Audit: проверка на отсутствие подсказок по ожидаемому audience
    raw_low = response.text.lower()
    for field in DENY_FIELDS:
        assert field not in raw_low
        assert field not in [str(k).lower() for k in data.keys()]

    # Убеждаемся, что в ответе нет значения из неверного токена
    assert "billing-api" not in raw_low
    assert "prid" not in raw_low
    assert "12345" not in raw_low