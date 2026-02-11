from responses import make_json_response

PROFILE_ID = "3fa85f64-5717-4562-b3fc-111111111111"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_050_sorting_independent_from_roles(
    mocker,
    api_client,
):
    # Базовая структура с упорядоченным массивом элементов
    viewer_body = {
        "profile_id": PROFILE_ID,
        "projects": [
            {"id": 1, "name": "Alpha"},
            {"id": 2, "name": "Beta"},
            {"id": 3, "name": "Gamma"},
        ],
    }

    # admin получает расширенные поля, но порядок элементов тот же
    admin_body = {
        "profile_id": PROFILE_ID,
        "projects": [
            {"id": 1, "name": "Alpha", "budget": 1000},
            {"id": 2, "name": "Beta", "budget": 2000},
            {"id": 3, "name": "Gamma", "budget": 3000},
        ],
    }

    resp_viewer = make_json_response(
        status=200,
        body=viewer_body,
        headers={
            "Content-Type": "application/json",
            "ETag": '"etag-viewer"',
            "X-Roles-Hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "Vary": "Authorization, X-Roles-Hash",
        },
    )

    resp_admin = make_json_response(
        status=200,
        body=admin_body,
        headers={
            "Content-Type": "application/json",
            "ETag": '"etag-admin"',
            "X-Roles-Hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "Vary": "Authorization, X-Roles-Hash",
        },
    )

    mock = mocker.patch("requests.Session.request")
    mock.side_effect = [resp_viewer, resp_admin]

    r_viewer = api_client.get(ENDPOINT, headers={"Authorization": "Bearer viewer"})
    r_admin = api_client.get(ENDPOINT, headers={"Authorization": "Bearer admin"})

    assert r_viewer.status_code == 200
    assert r_admin.status_code == 200

    viewer_projects = r_viewer.json()["projects"]
    admin_projects = r_admin.json()["projects"]

    # Проверка детерминированного порядка
    viewer_ids = [p["id"] for p in viewer_projects]
    admin_ids = [p["id"] for p in admin_projects]

    assert viewer_ids == admin_ids

    # Проверка что различаются только разрешенные поля
    assert "budget" not in viewer_projects[0]
    assert "budget" in admin_projects[0]

    # Проверка отсутствия запрещенных полей
    for forbidden in [
        "roles",
        "permissions",
        "scopes",
        "internalflags",
        "internalid",
        "stacktrace",
        "exception",
        "<html",
    ]:
        assert forbidden not in r_viewer.text.lower()
        assert forbidden not in r_admin.text.lower()
