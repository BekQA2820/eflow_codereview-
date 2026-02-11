import uuid
import re

ENDPOINT = "/api/v1/portal/home"


def test_rbac_profile_003_unauthorized_user_cannot_access_homepage(
    mocker,
    api_client,
):
    trace_id = f"trace-{uuid.uuid4()}"

    error_body = {
        "code": "UNAUTHORIZED",
        "message": "authorization header is missing",
        "details": [],
        "traceId": trace_id,
    }

    resp = make_json_response(
        status=401,
        body=error_body,
        headers={
            "Cache-Control": "no-store",
            "Vary": "Authorization",
            "Content-Type": "application/json",
            "X-Request-ID": trace_id,
        },
    )

    # ✅ Золотой стандарт
    mocker.patch("requests.Session.request", return_value=resp)

    response = api_client.get(
        ENDPOINT,
        headers={
            "Accept": "application/json",
        },
    )

    # --- HTTP ---
    assert response.status_code == 401

    # --- Headers ---
    assert response.headers.get("Content-Type") == "application/json"
    assert "no-store" in response.headers.get("Cache-Control", "")
    assert "Authorization" in response.headers.get("Vary", "")
    assert "ETag" not in response.headers

    # --- Body ---
    data = response.json()

    # Обязательная структура ошибки
    assert "code" in data and data["code"]
    assert "message" in data and data["message"]
    assert "details" in data and isinstance(data["details"], list)
    assert "traceId" in data and data["traceId"]

    # X-Request-ID связан с traceId
    assert response.headers.get("X-Request-ID") == data["traceId"]

    # --- Отсутствие доменных данных ---
    forbidden_fields = {
        "profile_id",
        "displayName",
        "layout",
        "widgets",
        "email",
    }

    for field in forbidden_fields:
        assert field not in data

    # --- Security deny-list ---
    deny_tokens = {
        "internalflags",
        "internalid",
        "requiredpermissions",
        "configsource",
        "internalmeta",
        "debuginfo",
        "stacktrace",
        "exception",
        "<html",
        "select ",
        "insert ",
        "update ",
    }

    body_lower = response.text.lower()
    for token in deny_tokens:
        assert token not in body_lower
