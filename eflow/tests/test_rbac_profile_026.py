import uuid
from responses import make_json_response

PROFILE_ID = "3fa85f64-5717-4562-b3fc-111111111111"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_026_deterministic_access_on_role_change(
    mocker,
    api_client,
):
    trace_id = str(uuid.uuid4())

    # --- 1. Ответ для restricted ---
    forbidden_body = {
        "code": "FORBIDDEN",
        "message": "Access denied",
        "details": [],
        "traceId": trace_id,
    }

    resp_forbidden = make_json_response(
        status=403,
        body=forbidden_body,
        headers={
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            "Vary": "Authorization, X-Roles-Hash",
            "X-Request-ID": trace_id,
        },
    )

    # --- 2. Ответ для viewer ---
    viewer_body = {
        "profile_id": PROFILE_ID,
        "displayName": "John Doe",
    }

    resp_allowed = make_json_response(
        status=200,
        body=viewer_body,
        headers={
            "Content-Type": "application/json",
            "ETag": '"abc123strong"',
            "Vary": "Authorization, X-Roles-Hash",
            "X-Roles-Hash": "d41d8cd98f00b204e9800998ecf8427e",
        },
    )

    mock = mocker.patch("requests.Session.request")
    mock.side_effect = [resp_forbidden, resp_allowed]

    # --- restricted ---
    r_forbidden = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer restricted"},
    )

    assert r_forbidden.status_code == 403
    body_403 = r_forbidden.json()
    assert body_403["code"] == "FORBIDDEN"
    assert "profile_id" not in r_forbidden.text.lower()

    # --- viewer ---
    r_allowed = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer viewer"},
    )

    assert r_allowed.status_code == 200
    body_200 = r_allowed.json()
    assert "displayName" in body_200

    # --- Cache isolation ---
    assert "Authorization" in r_allowed.headers.get("Vary", "")
    assert "X-Roles-Hash" in r_allowed.headers.get("Vary", "")
    assert r_allowed.headers.get("ETag") is not None
