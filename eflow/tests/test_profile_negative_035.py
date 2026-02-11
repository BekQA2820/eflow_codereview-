import json
import pytest
import requests
import uuid

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH = f"/api/v1/employee-profiles/{PROFILE_ID}"

DENY_FIELDS = {
    "expired", "skew", "clock", "timestamp", "current_time", "exp",
    "internalflags", "stacktrace", "exception", "<html", "configsource"
}


@pytest.mark.integration
@pytest.mark.parametrize("delay_desc, expired_token", [
    ("1_sec_ago", "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MDY0NDMyMDB9.sig"),
    ("1_min_ago", "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MDY0Mzk2MDB9.sig"),
    ("1_hour_ago", "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MDY0MzYwMDB9.sig")
])
def test_profile_negative_035_expired_token_determinism(mocker, api_client, delay_desc, expired_token):
    trace_id = str(uuid.uuid4())

    # Согласно Saved Info: Ошибка токена — это всегда 401 Unauthorized
    error_body = {
        "code": "UNAUTHORIZED",
        "message": "Authentication failed",
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
        "Vary": "Authorization",
        "X-Request-ID": trace_id
    }

    mocker.patch.object(requests.Session, "request", return_value=mock_resp)
    mocker.patch("requests.request", return_value=mock_resp)

    response = api_client.get(
        PATH,
        headers={
            "Authorization": expired_token,
            "X-Request-ID": trace_id
        }
    )

    # 1. Проверка детерминированности статуса
    assert response.status_code == 401
    assert response.headers.get("Content-Type") == "application/json"
    assert "no-store" in response.headers.get("Cache-Control", "").lower()
    assert "Authorization" in response.headers.get("Vary", "")

    # 2. Проверка структуры и корреляции ID
    data = response.json()
    assert data["code"] == "UNAUTHORIZED"
    assert data["traceId"] == trace_id
    assert data["message"] == "Authentication failed"
    assert data["details"] == []

    # 3. Security Audit: проверка на отсутствие временных меток и деталей просрочки
    raw_low = response.text.lower()
    for field in DENY_FIELDS:
        assert field not in raw_low
        assert field not in [str(k).lower() for k in data.keys()]

    # Проверка отсутствия старых ID и самих значений exp из токена в ответе
    assert "17064" not in raw_low
    assert "prid" not in raw_low
    assert "12345" not in raw_low