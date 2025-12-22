import pytest
from unittest.mock import Mock

MANIFEST = "/api/v1/manifest"


def test_rbac_public_widgets(mocker, api_client, auth_header):

    widgets = [
        {"id": "w1", "type": "mfe"},
        {"id": "w2", "type": "mfe", "requiredRoles": []},
    ]

    response = Mock()
    response.status_code = 200
    response.headers = {"Content-Type": "application/json"}
    response.json.return_value = {"widgets": widgets}

    mocker.patch("requests.get", return_value=response)

    roles_variants = [
        [],
        ["employee"],
        ["admin"],
        ["employee", "manager"]
    ]

    results = []

    for roles in roles_variants:
        hdr = {"X-Roles": ",".join(roles)}
        hdr.update(auth_header)
        r = api_client.get(MANIFEST, headers=hdr)

        assert r.status_code == 200
        assert r.headers["Content-Type"].startswith("application/json")

        data = r.json()
        assert "widgets" in data and isinstance(data["widgets"], list)

        results.append(data["widgets"])

    # Все варианты ролей должны видеть ОДИНАКОВЫЕ виджеты
    assert all(r == results[0] for r in results), "Public widgets должны быть одинаковыми для всех ролей"
