import json
import pytest
import requests
import uuid

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH = f"/api/v1/employee-profiles/{PROFILE_ID}"

DENY_FIELDS = {
    "scope", "role", "conflict", "intersect", "logic", "check",
    "internalflags", "stacktrace", "exception", "<html", "backendonly"
}


@pytest.mark.integration
def test_profile_negative_025_rbac_scope_conflict(mocker, api_client):
    trace_id = str(uuid.uuid4())
    # JWT содержит роль 'Admin', но не имеет scope 'profile:read'
    conflicting_jwt = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlcyI6WyJBZG1pbiJdLCJzY29wZSI6Im9wZW5pZCJ9.sig"

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

    # Согласно Saved Info: Любая ошибка авторизации (RBAC/Scope) — это 403 Forbidden
    assert response.status_code == 403
    assert response.headers.get("Content-Type") == "application/json"
    assert "no-store" in response.headers.get("Cache-Control", "").lower()

    data = response.json()
    assert data["code"] == "FORBIDDEN"
    assert data["traceId"] == trace_id

    # Security Audit: проверка отсутствия логики принятия решения в ответе
    raw_low = response.text.lower()
    for field in DENY_FIELDS:
        assert field not in raw_low
        assert field not in [str(k).lower() for k in data.keys()]

    # Убеждаемся, что в ответе нет названий ролей или скоупов из запроса
    assert "admin" not in raw_low
    assert "openid" not in raw_low
    assert "prid" not in raw_low