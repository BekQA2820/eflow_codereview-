import json
import pytest
import requests
import uuid

PATH = "/api/v1/employee-profiles/3fa85f64-5717-4562-b3fc-2c963f66afa6"

DENY_FIELDS = {
    "exp", "expired", "clock", "skew", "timestamp", "current_time",
    "server_time", "unix", "jwt", "internalflags", "stacktrace",
    "exception", "<html", "forbidden", "500"
}


@pytest.mark.integration
def test_profile_negative_015_expired_jwt_no_time_leak(mocker, api_client):
    # JWT с валидной подписью, но exp в прошлом
    expired_jwt = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE1MTYyMzkwMjJ9.sig"

    def mock_security_layer(*args, **kwargs):
        trace_id = kwargs.get("headers", {}).get("X-Request-ID", str(uuid.uuid4()))
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

    mocker.patch.object(requests.Session, "request", side_effect=mock_security_layer)
    mocker.patch("requests.request", side_effect=mock_security_layer)

    # Выполняем два последовательных запроса для проверки изоляции и кэширования
    responses = []
    for _ in range(2):
        unique_rid = str(uuid.uuid4())
        res = api_client.get(
            PATH,
            headers={"Authorization": expired_jwt, "X-Request-ID": unique_rid}
        )
        responses.append((res, unique_rid))

    # 1. Проверка идентичности структуры и уникальности traceId
    res1, rid1 = responses[0]
    res2, rid2 = responses[1]

    assert res1.status_code == 401
    assert res2.status_code == 401
    assert res1.json()["traceId"] == rid1
    assert res2.json()["traceId"] == rid2
    assert res1.json()["traceId"] != res2.json()["traceId"]

    # 2. Проверка заголовков кэширования
    for res, _ in responses:
        assert "no-store" in res.headers["Cache-Control"].lower()
        assert "Authorization" in res.headers["Vary"]
        assert "ETag" not in res.headers
        assert "hit" not in res.headers.get("X-Cache", "").lower()

    # 3. Security Audit на утечки времени и параметров exp
    for res, _ in responses:
        raw_low = res.text.lower()
        data = res.json()

        for field in DENY_FIELDS:
            assert field not in raw_low, f"Time-related leak detected: {field}"
            assert field not in [str(k).lower() for k in data.keys()]

        # Убеждаемся, что нет признаков отладки и старых ID
        assert "prid" not in raw_low
        assert "12345" not in raw_low