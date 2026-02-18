from responses import make_json_response

PROFILE_ID = "3fa85f64-5717-4562-b3fc-111111111111"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_008_limited_role_returns_partial_fields(
    mocker,
    api_client,
):
    body = {
        "profile_id": PROFILE_ID,
        "displayName": "John Doe",
    }

    resp = make_json_response(
        status=200,
        body=body,
        headers={
            "ETag": '"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"',
            "Cache-Control": "private, no-store",
            "Vary": "Authorization, X-Roles-Hash",
            "Content-Type": "application/json",
        },
    )

    mocker.patch("requests.Session.request", return_value=resp)

    r = api_client.get(
        ENDPOINT,
        headers={
            "Authorization": "Bearer jwt-limited-role",
            "Accept": "application/json",
        },
    )

    assert r.status_code == 200

    data = r.json()

    # --- Allowed fields only ---
    assert "profile_id" in data
    assert "displayName" in data

    # --- Forbidden fields ---
    forbidden_fields = [
        "email",
        "attributes",
        "relationships",
        "widgets",
        "layout",
        "theme",
        "locale",
    ]

    for field in forbidden_fields:
        assert field not in data

    # --- No null placeholders ---
    for value in data.values():
        assert value is not None

    # --- Headers ---
    assert not r.headers["ETag"].startswith("W/")
    assert "public" not in r.headers["Cache-Control"].lower()
