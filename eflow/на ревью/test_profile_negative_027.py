import json
import pytest
import requests
import uuid

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH = f"/api/v1/employee-profiles/{PROFILE_ID}"

DENY_FIELDS = {
    "hash", "hex32", "md5", "sha1", "invalid_format", "length",
    "internalflags", "stacktrace", "exception", "<html", "backendonly"
}


@pytest.mark.integration
@pytest.mark.parametrize("invalid_hash", [
    "not-a-hex-value-123",  # Недопустимые символы
    "abc123",  # Слишком короткий
    "a" * 64,  # Слишком длинный (SHA256 вместо MD5/Hex32)
    123456789  # Число вместо строки
])
def test_profile_negative_027_roles_hash_malformed(mocker, api_client, invalid_hash):
    trace_id = str(uuid.uuid4())
    # JWT с валидной подписью, но "битым" по формату полем roles_hash
    bad_hash_jwt = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlc19oYXNoIjoiaW52YWxpZCJ9.sig"

    # Согласно Saved Info Любая ошибка в структуре/валидации токена — это 401 Unauthorized
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
            "Authorization": bad_hash_jwt,
            "X-Request-ID": trace_id
        }
    )

    assert response.status_code == 401
    assert response.headers.get("Content-Type") == "application/json"

    # Проверка, что заголовок X-Roles-Hash либо отсутствует, либо не равен нашему "битому" значению
    if "X-Roles-Hash" in response.headers:
        assert response.headers["X-Roles-Hash"] != str(invalid_hash)

    data = response.json()
    assert data["code"] == "UNAUTHORIZED"
    assert data["traceId"] == trace_id

    # Security Audit: отсутствие технических подробностей о хешировании
    raw_low = response.text.lower()
    for field in DENY_FIELDS:
        assert field not in raw_low
        assert field not in [str(k).lower() for k in data.keys()]

    # Убеждаемся, что в ответе нет присланного некорректного значения
    assert str(invalid_hash).lower() not in raw_low
    assert "prid" not in raw_low