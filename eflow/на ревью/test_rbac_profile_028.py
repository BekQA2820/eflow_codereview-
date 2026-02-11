import re
from responses import make_json_response

PROFILE_ID = "3fa85f64-5717-4562-b3fc-111111111111"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_028_etag_depends_on_roles_and_isolated(
    mocker,
    api_client,
):
    # --- admin representation ---
    admin_body = {
        "profile_id": PROFILE_ID,
        "displayName": "John Doe",
        "email": "john.doe@example.com",
    }

    resp_admin = make_json_response(
        status=200,
        body=admin_body,
        headers={
            "Content-Type": "application/json",
            "ETag": '"etag-admin-strong"',
            "X-Roles-Hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "Vary": "Authorization, X-Roles-Hash",
            "Cache-Control": "private, max-age=60",
            "X-Cache": "MISS",
        },
    )

    # --- viewer representation ---
    viewer_body = {
        "profile_id": PROFILE_ID,
        "displayName": "John Doe",
    }

    resp_viewer = make_json_response(
        status=200,
        body=viewer_body,
        headers={
            "Content-Type": "application/json",
            "ETag": '"etag-viewer-strong"',
            "X-Roles-Hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "Vary": "Authorization, X-Roles-Hash",
            "Cache-Control": "private, max-age=60",
            "X-Cache": "MISS",
        },
    )

    mock = mocker.patch("requests.Session.request")
    mock.side_effect = [resp_admin, resp_viewer]

    # --- admin request ---
    r_admin = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer admin"},
    )

    assert r_admin.status_code == 200
    admin_etag = r_admin.headers.get("ETag")
    admin_hash = r_admin.headers.get("X-Roles-Hash")

    assert admin_etag is not None
    assert not admin_etag.startswith("W/")
    assert re.match(r"^[0-9a-f]{32}$", admin_hash)

    # --- viewer request ---
    r_viewer = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer viewer"},
    )

    assert r_viewer.status_code == 200
    viewer_etag = r_viewer.headers.get("ETag")
    viewer_hash = r_viewer.headers.get("X-Roles-Hash")

    # --- ETag differs ---
    assert admin_etag != viewer_etag
    assert viewer_etag is not None
    assert not viewer_etag.startswith("W/")
    assert re.match(r"^[0-9a-f]{32}$", viewer_hash)

    # --- Bodies differ ---
    assert r_admin.json() != r_viewer.json()
    assert "email" in r_admin.json()
    assert "email" not in r_viewer.json()

    # --- Cache isolation ---
    assert "Authorization" in r_admin.headers.get("Vary", "")
    assert "X-Roles-Hash" in r_admin.headers.get("Vary", "")
    assert "public" not in r_admin.headers.get("Cache-Control", "").lower()

    # --- Security scan ---
    raw = r_admin.text.lower() + r_viewer.text.lower()
    deny = ["roles", "permissions", "scopes", "internalflags", "stacktrace", "<html"]
    for token in deny:
        assert token not in raw
