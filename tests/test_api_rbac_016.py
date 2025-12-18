import json
import pytest

MANIFEST_PATH = "/api/v1/manifest"


def test_manifest_public_user_without_roles(mocker, api_client):
    """
    API RBAC 016
    Валидный токен без ролей → только public widgets
    """

    public_manifest = {
        "widgets": [
            {
                "id": "public-widget",
                "type": "mfe",
                "visible": True,
                "position": {"row": 0, "col": 0, "width": 2},
            }
        ],
        "layout": {"rows": 1, "columns": 2, "gridType": "fixed"},
        "version": "1",
    }

    response = mocker.Mock()
    response.status_code = 200
    response.headers = {
        "Content-Type": "application/json",
        "Vary": "Authorization, X-Roles",
        "X-Roles-Hash": "0" * 32,
        "X-Cache": "MISS",
        "X-Request-ID": "rbac-public-001",
    }
    response.json.return_value = public_manifest
    response.content = json.dumps(public_manifest).encode()

    mocker.patch("requests.get", return_value=response)

    token_without_roles = "jwt-without-roles-claim"

    r = api_client.get(
        MANIFEST_PATH,
        headers={"Authorization": f"Bearer {token_without_roles}"},
    )

    # -----------------------------
    # HTTP
    # -----------------------------
    assert r.status_code == 200
    assert r.headers["Content-Type"].startswith("application/json")
    assert r.headers.get("Vary") == "Authorization, X-Roles"

    # -----------------------------
    # RBAC
    # -----------------------------
    data = r.json()

    assert "widgets" in data
    assert isinstance(data["widgets"], list)
    assert len(data["widgets"]) == 1

    widget = data["widgets"][0]
    assert widget["id"] == "public-widget"
    assert widget["visible"] is True

    # -----------------------------
    # roles_hash
    # -----------------------------
    roles_hash = r.headers.get("X-Roles-Hash")
    assert isinstance(roles_hash, str)
    assert len(roles_hash) == 32
    assert roles_hash == "0" * 32
