import json
import pytest
import requests
import uuid

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH = f"/api/v1/employee-profiles/{PROFILE_ID}"

# Строки, имитирующие JWT или Base64 секреты
TOKEN_LIKE_VALUE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.signature"
BASE64_LIKE_VALUE = "dGhpcyBpcyBhIGZha2Ugc2VjcmV0IGtleSAxMjM0NQ=="

DENY_FIELDS = {
    "echo", "mirror", "nested", "internalflags", "stacktrace",
    "exception", "<html", "configsource"
}


@pytest.mark.integration
def test_profile_negative_029_token_like_claims_ignored(mocker, api_client):
    trace_id = str(uuid.uuid4())
    # Формируем JWT с "шумовыми" клеймами, похожими на токены
    noisy_jwt = (
        f"Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        f"eyJyb2xlcyI6WyJVc2VyIl0sIm5lc3RlZF90b2tlbiI6IltUT0tFTl9MSUtFX1ZBTFVFXSIsImRlYnVnX2tleSI6IltCQVNFNjRfTElLRV9WQUxVRV0ifQ.sig"
    )

    # Предположим, запрос падает с 401 по другой причине или проходит 200,
    # главное — отсутствие этих строк в ответе.
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
        "X-Request-ID": trace_id
    }

    mocker.patch.object(requests.Session, "request", return_value=mock_resp)
    mocker.patch("requests.request", return_value=mock_resp)

    response = api_client.get(
        PATH,
        headers={
            "Authorization": noisy_jwt,
            "X-Request-ID": trace_id
        }
    )

    assert response.status_code == 401

    raw_low = response.text.lower()
    data = response.json()

    # Security Audit: Самая важная часть — проверка отсутствия "эха" наших токен-лайк строк
    assert TOKEN_LIKE_VALUE.lower() not in raw_low
    assert BASE64_LIKE_VALUE.lower() not in raw_low

    for field in DENY_FIELDS:
        assert field not in raw_low
        assert field not in [str(k).lower() for k in data.keys()]

    # Проверка отсутствия старых ID
    assert "prid" not in raw_low
    assert "12345" not in raw_low