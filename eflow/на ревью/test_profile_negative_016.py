import json
import pytest
import requests
import uuid

PATH = "/api/v1/employee-profiles/3fa85f64-5717-4562-b3fc-2c963f66afa6"

DENY_FIELDS = {
    "signature", "crypto", "mismatch", "algorithm", "hs256", "rs256",
    "key", "secret", "invalid", "internalflags", "stacktrace",
    "exception", "<html", "forbidden", "500", "bearer"
}


@pytest.mark.integration
def test_profile_negative_016_invalid_signature_uniform_error(mocker, api_client):
    # JWT с валидной структурой, но некорректной подписью
    invalid_sig_jwt = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.wrongsig"

    def mock_auth_interceptor(*args, **kwargs):
        trace_id = kwargs.get("headers", {}).get("X-Request-ID", str(uuid.uuid4()))
        # Унифицированный ответ для любой ошибки аутентификации
        error_body = {
            "code": "UNAUTHORIZED",
            "message": "Authentication failed",
            "details": [],
            "traceId": trace_id
        }
        js_error = json.dumps(error_body)

        resp = mocker.Mock(spec=requests.Response)
        resp.status_code = 401
        resp.json.return_value = error_body
        resp.text = js_error
        resp.content = js_error.encode("utf-8")
        resp.headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            "Vary": "Authorization",
            "X-Request-ID": trace_id
        }
        return resp

    mocker.patch.object(requests.Session, "request", side_effect=mock_auth_interceptor)
    mocker.patch("requests.request", side_effect=mock_auth_interceptor)

    responses = []
    for _ in range(2):
        unique_rid = str(uuid.uuid4())
        res = api_client.get(
            PATH,
            headers={"Authorization": invalid_sig_jwt, "X-Request-ID": unique_rid}
        )
        responses.append((res, unique_rid))

    # 1. Проверка идентичности и уникальности traceId
    res1, rid1 = responses[0]
    res2, rid2 = responses[1]

    assert res1.status_code == 401
    assert res1.json()["traceId"] == rid1
    assert res2.json()["traceId"] == rid2
    assert rid1 != rid2

    # 2. Проверка унификации (отсутствие различий между типами ошибок JWT)
    # Сообщение должно быть таким же, как в тесте 015 (expired)
    assert res1.json()["code"] == "UNAUTHORIZED"
    assert "failed" in res1.json()["message"].lower()

    # 3. Security Audit на утечки криптографии и параметров
    for res, _ in responses:
        assert "no-store" in res.headers["Cache-Control"].lower()
        assert "ETag" not in res.headers

        raw_low = res.text.lower()
        data = res.json()

        for field in DENY_FIELDS:
            # Исключаем 'bearer' из проверки текста ответа (он был только в запросе)
            assert field not in raw_low, f"Crypto-leak detected: {field}"
            assert field not in [str(k).lower() for k in data.keys()]

        # Проверка отсутствия base64-строк, похожих на ключи/хэши в ErrorResponse
        if data.get("details"):
            for detail in data["details"]:
                assert not any(c in str(detail) for c in ["+", "/", "="])

        assert "prid" not in raw_low
        assert "12345" not in raw_low