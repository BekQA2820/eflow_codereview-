from responses import make_json_response

PROFILE_ID = "3fa85f64-5717-4562-b3fc-111111111111"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_041_guest_no_personal_data(
    mocker,
    api_client,
):
    error_body = {
        "code": "FORBIDDEN",
        "message": "access denied",
        "details": [],
        "traceId": "trace-guest-1",
    }

    resp = make_json_response(
        status=403,
        body=error_body,
        headers={
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            "Vary": "Authorization, X-Roles-Hash",
            "X-Request-ID": "trace-guest-1",
        },
    )

    mocker.patch("requests.Session.request", return_value=resp)

    r = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer guest"},
    )

    assert r.status_code == 403
    assert r.headers.get("Cache-Control") == "no-store"

    data = r.json()

    assert data.get("code") == "FORBIDDEN"
    assert data.get("message")
    assert isinstance(data.get("details"), list)
    assert data.get("traceId")

    raw = r.text.lower()

    forbidden_fields = [
        "displayname",
        "email",
        "phone",
        "profile_id",
        "internalflags",
        "internalid",
        "stacktrace",
        "exception",
        "debuginfo",
        "internalmeta",
        "<html",
    ]

    for token in forbidden_fields:
        assert token not in raw
