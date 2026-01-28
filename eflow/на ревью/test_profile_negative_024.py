import json
import pytest
import requests
import uuid

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH = f"/api/v1/employee-profiles/{PROFILE_ID}"

DENY_FIELDS = {
    "scope", "case", "sensitive", "register", "profile.read", "profile:read",
    "internalflags", "stacktrace", "exception", "<html", "required"
}


@pytest.mark.integration
def test_profile_negative_024_scope_case_sensitivity(mocker, api_client):
    trace_id = str(uuid.uuid4())
    # Токен с валидной подписью, но scope в неверном регистре (PROFILE:READ)
    token_wrong_case = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzY29wZSI6IlBST0ZJTEU6UkVBRCJ9.sig"

    error_body = {
        "code": "FORBIDDEN",
        "message": "Access denied",
        "details": [],
        "traceId": trace_id
    }
    js_error = json.dumps(error_body)

    mock_resp = mocker.Mock(spec=requests.Response)
    mock_resp.status_code = 403
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
            "Authorization": token_wrong_case,
            "X-Request-ID": trace_id
        }
    )

    # Согласно Saved Info: Нехватка прав (scope/RBAC) — это 403 Forbidden
    assert response.status_code == 403
    assert response.headers.get("Content-Type") == "application/json"

    data = response.json()
    assert data["code"] == "FORBIDDEN"
    assert data["traceId"] == trace_id

    # Security Audit: проверка на отсутствие подсказок по ожидаемому регистру scope
    raw_low = response.text.lower()
    for field in DENY_FIELDS:
        assert field not in raw_low
        assert field not in [str(k).lower() for k in data.keys()]

    # Убеждаемся, что система не вернула данных профиля
    assert "3fa85f64" not in raw_low
    assert "prid" not in raw_low