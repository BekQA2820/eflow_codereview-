import re


MANIFEST_PATH = "/api/v1/manifest"


def test_roles_hash_format_and_stability(mocker, api_client):
    roles_hash = "b" * 32

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
            {"id": "w1", "type": "mfe", "position": {"row": 0, "col": 0, "width": 1}}
        ],
        "layout": {"rows": 1, "columns": 1, "gridType": "fixed"},
        "version": "1",
    }

    mocker.patch("requests.get", return_value=resp)

    r1 = api_client.get(
        MANIFEST_PATH,
        headers={"Authorization": "Bearer token", "X-Roles": "employee"},
    )
    r2 = api_client.get(
        MANIFEST_PATH,
        headers={"Authorization": "Bearer token", "X-Roles": "employee"},
    )

    h1 = r1.headers.get("X-Roles-Hash")
    h2 = r2.headers.get("X-Roles-Hash")

    assert re.fullmatch(r"[0-9a-f]{32}", h1)
    assert h1 == h2
