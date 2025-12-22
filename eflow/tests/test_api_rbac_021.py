import re

MANIFEST_PATH = "/api/v1/manifest"


def test_manifest_differs_for_large_roles_set(mocker, api_client):
    def make_response(widgets, roles_hash):
        resp = mocker.Mock()
        resp.status_code = 200
        resp.headers = {
            "Content-Type": "application/json",
            "X-Roles-Hash": roles_hash,
            "X-Cache": "MISS",
            "Vary": "Authorization, X-Roles",
        }
        resp.json.return_value = {
            "widgets": widgets,
            "layout": {"rows": 1, "columns": 3, "gridType": "fixed"},
            "version": "1",
        }
        return resp

    r_employee = make_response(
        [{"id": "public"}, {"id": "employee"}],
        "1" * 32,
    )
    r_admin = make_response(
        [{"id": "public"}, {"id": "admin"}],
        "2" * 32,
    )
    r_both = make_response(
        [{"id": "public"}, {"id": "employee"}, {"id": "admin"}],
        "3" * 32,
    )

    mocker.patch("requests.get", side_effect=[r_employee, r_admin, r_both])

    r1 = api_client.get(MANIFEST_PATH, headers={"X-Roles": "employee"})
    r2 = api_client.get(MANIFEST_PATH, headers={"X-Roles": "admin"})
    r3 = api_client.get(MANIFEST_PATH, headers={"X-Roles": "EMPLOYEE,Admin"})

    ids1 = {w["id"] for w in r1.json()["widgets"]}
    ids2 = {w["id"] for w in r2.json()["widgets"]}
    ids3 = {w["id"] for w in r3.json()["widgets"]}

    assert ids1 == {"public", "employee"}
    assert ids2 == {"public", "admin"}
    assert ids3 == {"public", "employee", "admin"}

    assert re.fullmatch(r"[0-9a-f]{32}", r1.headers["X-Roles-Hash"])
    assert re.fullmatch(r"[0-9a-f]{32}", r2.headers["X-Roles-Hash"])
    assert re.fullmatch(r"[0-9a-f]{32}", r3.headers["X-Roles-Hash"])
