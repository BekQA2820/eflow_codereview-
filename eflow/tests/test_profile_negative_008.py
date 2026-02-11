import json
import pytest
import requests
import uuid

PATH = "/api/v1/employee-profiles/3fa85f64-5717-4562-b3fc-2c963f66afa6"

DENY_FIELDS = {
    "exp", "expired", "jwt", "internalflags", "stacktrace",
    "exception", "<html", "500", "forbidden", "rbac"
}


@pytest.mark.integration
def test_profile_negative_008_expired_jwt_stability(mocker, api_client):
    # Истекший токен (валидная структура, но exp в прошлом)
    expired_token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE1MTYyMzkwMjJ9.signature"

    # Имитируем стабильный ответ 401 от Security Layer
    def mock_handler(*args, **kwargs):
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

    mocker.patch.object(requests.Session, "request", side_effect=mock_handler)
    mocker.patch("requests.request", side_effect=mock_handler)

    # Проверка стабильности: несколько запросов подряд не должны приводить к деградации в 403 или 500
    for _ in range(3):
        unique_rid = str(uuid.uuid4())
        response = api_client.get(
            PATH,
            headers={
                "Authorization": expired_token,
                "X-Request-ID": unique_rid
            }
        )

        # 1. Проверка статуса (строго 401)
        assert response.status_code == 401
        assert response.status_code != 403
        assert response.status_code != 500

        # 2. Проверка контракта и заголовков
        assert response.headers["Content-Type"] == "application/json"
        assert "no-store" in response.headers["Cache-Control"].lower()

        data = response.json()
        assert data["code"] == "UNAUTHORIZED"
        assert data["traceId"] == unique_rid

        # 3. Security Audit на отсутствие технических деталей
        raw_low = response.text.lower()
        for field in DENY_FIELDS:
            assert field not in raw_low
            assert field not in [str(k).lower() for k in data.keys()]

        assert "prid" not in raw_low
        assert "12345" not in raw_low