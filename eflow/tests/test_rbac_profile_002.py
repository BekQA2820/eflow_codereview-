import json
import re
import uuid

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_002_equivalent_roles_deterministic_response(
    mocker,
    api_client,
):
    trace_id = f"trace-{uuid.uuid4()}"

    # Эквивалентный нормализованный хеш ролей (md5-подобный формат)
    roles_hash = "9f86d081884c7d659a2feaa0c55ad015"

    body = {
        "code": "OK",
        "message": "success",
        "details": [],
        "traceId": trace_id,
        "profile_id": PROFILE_ID,
        "displayName": "John Doe",
        "email": "john.doe@corp.local",
    }

    resp = make_json_response(
        status=200,
        body=body,
        headers={
            "ETag": "etag-roles-normalized-001",
            "X-Roles-Hash": roles_hash,
            "X-Cache": "MISS",
            "Vary": "Authorization, X-Roles-Hash",
            "X-Request-ID": trace_id,
        },
    )

    # ✅ Золотой стандарт — патчим requests.Session.request
    mocker.patch("requests.Session.request", return_value=resp)

    # --- JWT-1: ["employee_basic","viewer"] ---
    r1 = api_client.get(
        ENDPOINT,
        headers={
            "Authorization": "Bearer token-1",
            "Accept": "application/json",
            "X-Roles": json.dumps(["employee_basic", "viewer"]),
        },
    )

    # --- JWT-2: ["viewer","employee_basic"] ---
    r2 = api_client.get(
        ENDPOINT,
        headers={
            "Authorization": "Bearer token-2",
            "Accept": "application/json",
            "X-Roles": json.dumps(["viewer", "employee_basic"]),
        },
    )

    # --- HTTP ---
    assert r1.status_code == 200
    assert r2.status_code == 200

    data1 = r1.json()
    data2 = r2.json()

    # --- Обертка API обязательна ---
    for data in (data1, data2):
        assert "code" in data and data["code"]
        assert "message" in data and data["message"]
        assert "traceId" in data and data["traceId"]

    # --- Тело полностью детерминировано ---
    assert data1 == data2

    # --- Заголовки ---
    assert r1.headers.get("ETag") == r2.headers.get("ETag")

    hash1 = r1.headers.get("X-Roles-Hash")
    hash2 = r2.headers.get("X-Roles-Hash")

    assert hash1 == hash2
    assert re.fullmatch(r"[0-9a-f]{32}", hash1)

    for r in (r1, r2):
        vary = r.headers.get("Vary", "")
        assert "Authorization" in vary
        assert "X-Roles-Hash" in vary

    # --- Кэш детерминирован ---
    assert r1.headers.get("X-Cache") == r2.headers.get("X-Cache")

    # --- В теле отсутствуют запрещенные поля ---
    forbidden_fields = {"roles", "permissions", "scopes"}
    for field in forbidden_fields:
        assert field not in data1
        assert field not in data2

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
    }

    body_lower = r1.text.lower()
    for token in deny_tokens:
        assert token not in body_lower
