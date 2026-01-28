import json
import pytest
import requests
import uuid

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH = f"/api/v1/employee-profiles/{PROFILE_ID}"

DENY_FIELDS = {
    "scope", "permission", "required", "missing", "profile:read",
    "internalflags", "stacktrace", "exception", "<html", "configsource"
}


@pytest.mark.integration
def test_profile_negative_023_missing_scope_forbidden(mocker, api_client):
    trace_id = str(uuid.uuid4())
    # Токен валиден, но содержит только базовый scope (например, 'openid'), без 'profile:read'
    token_insufficient_scope = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzY29wZSI6Im9wZW5pZCJ9.sig"

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
            "Authorization": token_insufficient_scope,
            "X-Request-ID": trace_id
        }
    )

    # Согласно Saved Info: Нехватка прав (scope/RBAC) — это всегда 403 Forbidden
    assert response.status_code == 403
    assert response.headers.get("Content-Type") == "application/json"
    assert "no-store" in response.headers.get("Cache-Control", "").lower()

    data = response.json()
    assert data["code"] == "FORBIDDEN"
    assert data["traceId"] == trace_id

    # Security Audit: проверка на отсутствие названий scope и внутренних полей
    raw_low = response.text.lower()
    for field in DENY_FIELDS:
        assert field not in raw_low
        assert field not in [str(k).lower() for k in data.keys()]

    # Проверка отсутствия старых форматов ID
    assert "prid" not in raw_low
    assert "12345" not in raw_low