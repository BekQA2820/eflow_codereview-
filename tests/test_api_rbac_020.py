import re

MANIFEST_PATH = "/api/v1/manifest"


def test_acl_cache_uses_normalized_roles(mocker, api_client):
    roles_hash = "c" * 32

    def make_response(x_cache):
        resp = mocker.Mock()
        resp.status_code = 200
        resp.headers = {
            "Content-Type": "application/json",
            "X-Roles-Hash": roles_hash,
            "X-Cache": x_cache,
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

    mocker.patch(
        "requests.get",
        side_effect=[
            make_response("MISS"),
            make_response("HIT"),
            make_response("HIT"),
            make_response("HIT"),
        ],
    )

    role_variants = ["employee", "employee,employee", "EMPLOYEE", "Employee"]

    hashes = set()

    for roles in role_variants:
        r = api_client.get(
            MANIFEST_PATH,
            headers={"Authorization": "Bearer token", "X-Roles": roles},
        )
        rh = r.headers.get("X-Roles-Hash")
        assert re.fullmatch(r"[0-9a-f]{32}", rh)
        hashes.add(rh)

    assert hashes == {roles_hash}
