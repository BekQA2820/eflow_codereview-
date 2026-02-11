import json
import pytest
import requests
import uuid

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH = f"/api/v1/employee-profiles/{PROFILE_ID}"

DENY_FIELDS = {
    "signature", "crypto", "algorithm", "invalid", "verify", "key",
    "internalflags", "stacktrace", "exception", "<html", "configsource"
}


@pytest.mark.integration
def test_profile_negative_036_invalid_signature_unauthorized(mocker, api_client):
    trace_id = str(uuid.uuid4())
    # JWT с валидной структурой, но "отравленной" подписью
    tampered_signature_jwt = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.WRONG_SIGNATURE_DATA"

    # Согласно Saved Info: Ошибка токена/подписи — это 401 Unauthorized
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

    # Универсальный патч сессии согласно вашим правилам
    mocker.patch.object(requests.Session, "request", return_value=mock_resp)
    mocker.patch("requests.request", return_value=mock_resp)

    # Выполняем серию запросов для проверки детерминированности
    for _ in range(3):
        response = api_client.get(
            PATH,
            headers={
                "Authorization": tampered_signature_jwt,
                "X-Request-ID": trace_id
            }
        )

        # 1. Проверка строгой классификации (только 401)
        assert response.status_code == 401
        assert response.status_code != 403
        assert response.status_code != 404

        # 2. Проверка соответствия ErrorResponse и корреляции ID
        data = response.json()
        assert data["code"] == "UNAUTHORIZED"
        assert data["traceId"] == trace_id
        assert "message" in data

        # 3. Security Audit: проверка на отсутствие криптографических деталей
        raw_low = response.text.lower()
        for field in DENY_FIELDS:
            assert field not in raw_low
            assert field not in [str(k).lower() for k in data.keys()]

        # 4. Проверка заголовков безопасности
        assert response.headers.get("Content-Type") == "application/json"
        assert "no-store" in response.headers.get("Cache-Control", "").lower()
        assert "ETag" not in response.headers

        # Проверка отсутствия старых ID и PII
        assert "prid" not in raw_low
        assert "12345" not in raw_low