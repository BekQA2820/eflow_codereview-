import json

MANIFEST_PATH = "/api/v1/manifest"


def test_manifest_identical_for_users_with_same_roles(mocker, api_client):
    """
    API LAYOUT 005
    Разные пользователи с одинаковыми ролями получают идентичный manifest
    """

    manifest = {
        "layout": {"rows": 2, "columns": 3, "gridType": "fixed"},
        "widgets": [
            {
                "id": "public-widget",
                "type": "mfe",
                "visible": True,
                "position": {"row": 0, "col": 0, "width": 1},
            },
            {
                "id": "employee-widget",
                "type": "link",
                "visible": True,
                "position": {"row": 0, "col": 1, "width": 2},
            },
        ],
        "version": "5",
    }

    def make_resp():
        r = mocker.Mock()
        r.status_code = 200
        r.headers = {
            "Content-Type": "application/json",
            "Vary": "Authorization, X-Roles",
            "X-Roles-Hash": "e" * 32,
        }
        r.json.return_value = manifest
        r.text = json.dumps(manifest)
        return r

    mocker.patch("requests.get", side_effect=[make_resp(), make_resp()])

    r1 = api_client.get(
        MANIFEST_PATH,
        headers={"Authorization": "Bearer user-a"},
    )

    r2 = api_client.get(
        MANIFEST_PATH,
        headers={"Authorization": "Bearer user-b"},
    )

    assert r1.json() == r2.json()
    assert r1.headers["X-Roles-Hash"] == r2.headers["X-Roles-Hash"]
    assert r1.headers["Vary"] == "Authorization, X-Roles"
