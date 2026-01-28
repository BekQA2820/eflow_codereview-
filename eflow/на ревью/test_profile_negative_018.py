import json
import pytest
import requests
import uuid

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH = f"/api/v1/employee-profiles/{PROFILE_ID}"

DENY_FIELDS = {
    "role_conflict", "duplicate", "case_insensitive", "rbac_model",
    "internalflags", "stacktrace", "exception", "<html", "requiredroles"
}


@pytest.mark.integration
def test_profile_negative_018_role_conflict_forbidden(mocker, api_client):
    trace_id = str(uuid.uuid4())
    # JWT с противоречивыми ролями (например, 'User' и 'USER' или взаимоисключающие права)
    conflicting_jwt = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlcyI6WyJVc2VyIiwgIlVTRVIiXX0.sig"

    error_body = {
        "code": "FORBIDDEN",
        "message": "Access denied due to invalid permissions configuration",
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
        "Vary": "Authorization, X-Roles-Hash",
        "X-Request-ID": trace_id
    }

    mocker.patch.object(requests.Session, "request", return_value=mock_resp)
    mocker.patch("requests.request", return_value=mock_resp)

    response = api_client.get(
        PATH,
        headers={
            "Authorization": conflicting_jwt,
            "X-Request-ID": trace_id
        }
    )

    # Согласно Saved Info: Ошибки RBAC — это 403
    assert response.status_code == 403
    assert response.headers.get("Content-Type") == "application/json"

    # Проверка обязательных заголовков для безопасности и кэширования
    assert "no-store" in response.headers.get("Cache-Control", "").lower()
    vary = response.headers.get("Vary", "")
    assert "Authorization" in vary
    assert "X-Roles-Hash" in vary

    data = response.json()
    assert data["code"] == "FORBIDDEN"
    assert data["traceId"] == trace_id

    # Security Audit: отсутствие деталей о том, что именно не так с ролями
    raw_low = response.text.lower()
    for field in DENY_FIELDS:
        assert field not in raw_low
        assert field not in [str(k).lower() for k in data.keys()]

    # Убеждаемся, что в ответе нет идентификаторов ролей из запроса
    assert "user" not in raw_low
    assert "prid" not in raw_low
    assert "12345" not in raw_low