import re


MANIFEST_PATH = "/api/v1/manifest"


def test_roles_normalization_produces_same_roles_hash(mocker, api_client):
    roles_hash = "a" * 32

    def make_response():
        resp = mocker.Mock()
        resp.status_code = 200
        resp.headers = {
            "Content-Type": "application/json",
            "X-Roles-Hash": roles_hash,
            "X-Cache": "HIT",
            "Vary": "Authorization, X-Roles",
        }
        resp.json.return_value = {
            "widgets": [
                {"id": "public", "type": "mfe", "position": {"row": 0, "col": 0, "width": 1}}
            ],
            "layout": {"rows": 1, "columns": 1, "gridType": "fixed"},
            "version": "1",
        }
        return resp

    mocker.patch("requests.get", side_effect=[
        make_response(),
        make_response(),
        make_response(),
        make_response(),
    ])

    role_sets = [
        "Admin,employee",
        "employee,Admin",
        "EMPLOYEE,admin",
        "employee,admin,admin",
    ]

    hashes = set()

    for roles in role_sets:
        r = api_client.get(
            MANIFEST_PATH,
            headers={"Authorization": "Bearer token", "X-Roles": roles},
        )
        rh = r.headers.get("X-Roles-Hash")
        assert re.fullmatch(r"[0-9a-f]{32}", rh)
        hashes.add(rh)

    assert len(hashes) == 1, "Нормализованные роли должны давать одинаковый roles_hash"
