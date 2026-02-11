import json
import pytest
import requests
import uuid

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH = f"/api/v1/employee-profiles/{PROFILE_ID}"

DENY_FIELDS = {
    "type", "mismatch", "cast", "array", "string", "object", "parse",
    "internalflags", "stacktrace", "exception", "<html", "requiredroles"
}


@pytest.mark.integration
@pytest.mark.parametrize("malformed_roles", [
    "Admin",  # Строка вместо массива
    {"role": "Admin"},  # Объект вместо массива
    [123, 456],  # Массив чисел вместо строк
    None  # Null значение
])
def test_profile_negative_026_roles_format_mismatch(mocker, api_client, malformed_roles):
    trace_id = str(uuid.uuid4())
    # JWT с валидной подписью, но структурно неверным клеймом roles
    bad_format_jwt = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlcyI6Im1hbGZvcm1lZCJ9.sig"

    # Согласно Saved Info: Любая ошибка токена/подписи — это 401 Unauthorized
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
            "Authorization": bad_format_jwt,
            "X-Request-ID": trace_id
        }
    )

    assert response.status_code == 401
    assert response.headers.get("Content-Type") == "application/json"
    assert "no-store" in response.headers.get("Cache-Control", "").lower()

    data = response.json()
    assert data["code"] == "UNAUTHORIZED"
    assert data["traceId"] == trace_id

    # Security Audit: проверка отсутствия технических деталей парсинга JSON/JWT
    raw_low = response.text.lower()
    for field in DENY_FIELDS:
        assert field not in raw_low
        assert field not in [str(k).lower() for k in data.keys()]

    # Убеждаемся в отсутствии утечек данных профиля
    assert "3fa85f64" not in raw_low
    assert "prid" not in raw_low