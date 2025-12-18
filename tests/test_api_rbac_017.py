import json
import pytest

MANIFEST_PATH = "/api/v1/manifest"


def test_manifest_differs_for_different_roles(mocker, api_client):
    """
    API RBAC 017
    Проверка, что RBAC реально влияет на содержимое manifest,
    а не только на roles_hash и кэш.
    """

    manifest_employee = {
        "widgets": [
            {"id": "public", "type": "mfe", "position": {"row": 0, "col": 0, "width": 1}},
            {"id": "employee", "type": "mfe", "position": {"row": 0, "col": 1, "width": 1}},
        ],
        "layout": {"rows": 1, "columns": 2, "gridType": "fixed"},
        "version": "1",
    }

    manifest_admin = {
        "widgets": [
            {"id": "public", "type": "mfe", "position": {"row": 0, "col": 0, "width": 1}},
            {"id": "admin", "type": "mfe", "position": {"row": 0, "col": 1, "width": 1}},
        ],
        "layout": {"rows": 1, "columns": 2, "gridType": "fixed"},
        "version": "1",
    }

    def make_response(body, roles_hash):
        resp = mocker.Mock()
        resp.status_code = 200
        resp.headers = {
            "Content-Type": "application/json",
            "Vary": "Authorization, X-Roles",
            "X-Roles-Hash": roles_hash,
            "X-Cache": "MISS",
        }
        resp.json.return_value = body
        resp.content = json.dumps(body).encode("utf-8")
        return resp

    r_employee = make_response(manifest_employee, "e" * 32)
    r_admin = make_response(manifest_admin, "a" * 32)

    mock_get = mocker.patch("requests.get", side_effect=[r_employee, r_admin])

    # -------- employee --------
    r1 = api_client.get(
        MANIFEST_PATH,
        headers={"Authorization": "Bearer token-employee"},
    )

    # -------- admin --------
    r2 = api_client.get(
        MANIFEST_PATH,
        headers={"Authorization": "Bearer token-admin"},
    )

    widgets_employee = {w["id"] for w in r1.json()["widgets"]}
    widgets_admin = {w["id"] for w in r2.json()["widgets"]}

    # -------- assertions --------
    assert widgets_employee == {"public", "employee"}
    assert widgets_admin == {"public", "admin"}
    assert widgets_employee != widgets_admin, "RBAC должен влиять на набор виджетов"

    assert r1.headers["Vary"] == "Authorization, X-Roles"
    assert r2.headers["Vary"] == "Authorization, X-Roles"

    assert mock_get.call_count == 2
