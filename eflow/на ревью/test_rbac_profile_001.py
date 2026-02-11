import json
import uuid

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PROFILE_ENDPOINT = f"/employee-profiles/{PROFILE_ID}"


def test_rbac_profile_001_isolation_between_roles(
    mocker,
    api_client,
):
    trace_basic = f"trace-{uuid.uuid4()}"
    trace_extended = f"trace-{uuid.uuid4()}"

    # --- RESPONSE: employee_basic ---
    basic_body = {
        "code": "OK",
        "message": "success",
        "details": [],
        "traceId": trace_basic,
        "profile_id": PROFILE_ID,
        "displayName": "John Doe",
        # email отсутствует
        "roles": ["employee_basic"],
    }

    # --- RESPONSE: employee_extended ---
    extended_body = {
        "code": "OK",
        "message": "success",
        "details": [],
        "traceId": trace_extended,
        "profile_id": PROFILE_ID,
        "displayName": "John Doe",
        "email": "john.doe@corp.local",
        "roles": ["employee_extended"],
    }

    resp_basic = make_json_response(
        status=200,
        body=basic_body,
        headers={
            "ETag": "etag-basic-123",
            "Vary": "Authorization, X-Roles-Hash",
            "X-Cache": "MISS",
            "X-Request-ID": trace_basic,
        },
    )

    resp_extended = make_json_response(
        status=200,
        body=extended_body,
        headers={
            "ETag": "etag-extended-456",
            "Vary": "Authorization, X-Roles-Hash",
            "X-Cache": "MISS",
            "X-Request-ID": trace_extended,
        },
    )

    # --- ПАТЧ ПО ЗОЛОТОМУ СТАНДАРТУ ---
    def side_effect(self, method, url, **kwargs):
        roles = kwargs.get("headers", {}).get("X-Roles")
        if roles and "employee_extended" in roles:
            return resp_extended
        return resp_basic

    mocker.patch("requests.request", side_effect=side_effect)

    # --- ВЫЗОВ 1: employee_basic ---
    r_basic = api_client.get(
        PROFILE_ENDPOINT,
        headers={
            "X-Roles": json.dumps(["employee_basic"]),
        },
    )

    # --- ВЫЗОВ 2: employee_extended ---
    r_extended = api_client.get(
        PROFILE_ENDPOINT,
        headers={
            "X-Roles": json.dumps(["employee_extended"]),
        },
    )

    # --- ОБЩИЕ ПРОВЕРКИ ---
    assert r_basic.status_code == 200
    assert r_extended.status_code == 200

    data_basic = r_basic.json()
    data_extended = r_extended.json()

    # --- ОБЯЗАТЕЛЬНЫЕ ПОЛЯ ОБЕРТКИ ---
    for data in (data_basic, data_extended):
        assert "code" in data and data["code"]
        assert "message" in data and data["message"]
        assert "traceId" in data and data["traceId"]

    # --- RBAC ИЗОЛЯЦИЯ ---
    assert "email" not in data_basic
    assert "email" in data_extended

    # поля не должны быть null
    assert data_extended["email"] is not None

    # --- ETag должен различаться ---
    assert r_basic.headers.get("ETag") != r_extended.headers.get("ETag")

    # --- Vary обязателен ---
    for r in (r_basic, r_extended):
        vary = r.headers.get("Vary", "")
        assert "Authorization" in vary
        assert "X-Roles-Hash" in vary

    # --- X-Cache не reuse между ролями ---
    assert r_basic.headers.get("X-Cache") != "HIT"
    assert r_extended.headers.get("X-Cache") != "HIT"

    # --- SECURITY / DENY LIST ---
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
    }

    for r in (r_basic, r_extended):
        body_lower = r.text.lower()
        for token in deny_tokens:
            assert token not in body_lower
