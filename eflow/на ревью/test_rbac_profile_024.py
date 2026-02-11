import uuid
from responses import make_json_response

PROFILE_ID_EXISTING = "3fa85f64-5717-4562-b3fc-111111111111"
PROFILE_ID_MISSING = "3fa85f64-5717-4562-b3fc-000000000000"

ENDPOINT_EXISTING = f"/api/v1/profile/{PROFILE_ID_EXISTING}"
ENDPOINT_MISSING = f"/api/v1/profile/{PROFILE_ID_MISSING}"


def test_rbac_profile_024_no_side_effect_leak_on_forbidden(
    mocker,
    api_client,
):
    trace_id = str(uuid.uuid4())

    error_body = {
        "code": "FORBIDDEN",
        "message": "Access denied",
        "details": [],
        "traceId": trace_id,
    }

    resp = make_json_response(
        status=403,
        body=error_body,
        headers={
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            "Vary": "Authorization, X-Roles-Hash",
            "X-Request-ID": trace_id,
        },
    )

    mock = mocker.patch("requests.Session.request")
    mock.side_effect = [resp, resp]

    r_existing = api_client.get(
        ENDPOINT_EXISTING,
        headers={"Authorization": "Bearer restricted"},
    )

    r_missing = api_client.get(
        ENDPOINT_MISSING,
        headers={"Authorization": "Bearer restricted"},
    )

    # --- STATUS ---
    assert r_existing.status_code == 403
    assert r_missing.status_code == 403

    # --- HEADERS (сравнение набора и значений) ---
    assert r_existing.headers.get("Content-Type") == "application/json"
    assert r_missing.headers.get("Content-Type") == "application/json"

    assert r_existing.headers.get("Cache-Control") == "no-store"
    assert r_missing.headers.get("Cache-Control") == "no-store"

    assert r_existing.headers.get("Vary") == r_missing.headers.get("Vary")
    assert "Authorization" in r_existing.headers.get("Vary", "")
    assert "X-Roles-Hash" in r_existing.headers.get("Vary", "")

    assert "ETag" not in r_existing.headers
    assert "ETag" not in r_missing.headers

    # --- BODY ---
    body_existing = r_existing.json()
    body_missing = r_missing.json()

    assert body_existing["code"] == body_missing["code"] == "FORBIDDEN"
    assert body_existing["message"] == body_missing["message"]
    assert isinstance(body_existing.get("details"), list)
    assert isinstance(body_missing.get("details"), list)

    # структура одинаковая
    assert set(body_existing.keys()) == set(body_missing.keys())

    # --- SECURITY DENY LIST ---
    for response in (r_existing, r_missing):
        raw = response.text.lower()
        for forbidden in [
            "profile_id",
            "displayname",
            "email",
            "layout",
            "widgets",
            "internalflags",
            "internalid",
            "stacktrace",
            "exception",
            "<html",
        ]:
            assert forbidden not in raw
