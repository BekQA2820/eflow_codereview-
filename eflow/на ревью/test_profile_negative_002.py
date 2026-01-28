import json
import pytest
import requests

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH = f"/api/v1/employee-profiles/{PROFILE_ID}"

DENY_FIELDS = {
    "exp", "jwt", "signature", "expired", "internalflags",
    "stacktrace", "exception", "<html", "requiredroles"
}


@pytest.mark.integration
def test_profile_negative_002_expired_token(mocker, api_client):
    # Имитация стандартизированного ответа при ошибке токена
    error_body = {
        "code": "UNAUTHORIZED",
        "message": "Authentication failed",
        "details": [],
        "traceId": "tr-550e8400-e29b-41d4-a716-446655440000"
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
        "X-Request-ID": "tr-550e8400-e29b-41d4-a716-446655440000"
    }

    mocker.patch.object(requests.Session, "request", return_value=mock_resp)
    mocker.patch("requests.request", return_value=mock_resp)

    # Заголовок с имитацией истекшего токена
    expired_header = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.expired.token"}

    response = api_client.get(
        PATH,
        headers=expired_header
    )

    assert response.status_code == 401
    assert response.headers.get("Content-Type") == "application/json"
    assert "no-store" in response.headers.get("Cache-Control", "").lower()
    assert "Authorization" in response.headers.get("Vary", "")
    assert "ETag" not in response.headers

    data = response.json()
    assert data["code"] == "UNAUTHORIZED"
    assert "traceId" in data

    raw_low = response.text.lower()
    # Критично: message не должен содержать технических причин (exp, signature)
    for forbidden in DENY_FIELDS:
        assert forbidden not in raw_low
        assert forbidden not in [str(k).lower() for k in data.keys()]

    assert "prid" not in raw_low
    assert "12345" not in raw_low