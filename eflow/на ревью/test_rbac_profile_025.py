from responses import make_json_response

PROFILE_ID = "3fa85f64-5717-4562-b3fc-111111111111"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_025_unknown_roles_do_not_expand_access(
    mocker,
    api_client,
):
    # Базовый viewer-ответ
    viewer_body = {
        "profile_id": PROFILE_ID,
        "displayName": "John Doe",
    }

    resp_viewer = make_json_response(
        status=200,
        body=viewer_body,
        headers={
            "Content-Type": "application/json",
            "X-Roles-Hash": "d41d8cd98f00b204e9800998ecf8427e",
        },
    )

    resp_mixed = make_json_response(
        status=200,
        body=viewer_body,
        headers={
            "Content-Type": "application/json",
            "X-Roles-Hash": "d41d8cd98f00b204e9800998ecf8427e",
        },
    )

    mock = mocker.patch("requests.Session.request")
    mock.side_effect = [resp_viewer, resp_mixed]

    r_viewer = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer viewer"},
    )

    r_mixed = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer viewer+super_admin_internal"},
    )

    assert r_viewer.status_code == 200
    assert r_mixed.status_code == 200

    data_viewer = r_viewer.json()
    data_mixed = r_mixed.json()

    # --- Поля идентичны ---
    assert data_viewer == data_mixed

    # --- Нет расширения доступа ---
    for forbidden in ["roles", "permissions", "scopes"]:
        assert forbidden not in data_mixed

    raw = r_mixed.text.lower()
    for forbidden in [
        "internalflags",
        "internalid",
        "stacktrace",
        "exception",
    ]:
        assert forbidden not in raw

    # --- X-Roles-Hash соответствует только валидной роли ---
    assert r_viewer.headers.get("X-Roles-Hash") == r_mixed.headers.get("X-Roles-Hash")
