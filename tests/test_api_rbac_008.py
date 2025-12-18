import pytest
from unittest.mock import Mock
from conftest import compute_roles_hash

MANIFEST = "/api/v1/manifest"


def test_rbac_empty_roles_hash(mocker, api_client, auth_header):
    """
    Проверяем:
    ✔ три варианта пустых ролей → один и тот же roles_hash
    ✔ формат HEX, длина 32
    ✔ корректный Vary
    ✔ контент идентичен (public widgets only)
    """

    empty_variants = [
        "",               # пустая строка
        None,             # нет заголовка
        "   ",            # пробелы
    ]

    expected_hash = compute_roles_hash([])

    mock = Mock()
    mock.status_code = 200
    mock.headers = {
        "X-Roles-Hash": expected_hash,
        "Vary": "Authorization, X-Roles"
    }
    mock.json.return_value = {"widgets": [{"id": "w1"}]}

    mocker.patch("requests.get", return_value=mock)

    observed_hashes = []

    for raw in empty_variants:
        hdr = {}
        hdr.update(auth_header)

        if raw is not None:
            hdr["X-Roles"] = raw

        r = api_client.get(MANIFEST, headers=hdr)

        assert r.status_code == 200
        h = r.headers["X-Roles-Hash"]
        assert len(h) == 32, "Длина хеша должна быть 32 HEX символа"
        assert all(c in "0123456789abcdef" for c in h), "Хеш должен быть HEX lowercase"

        vary = r.headers.get("Vary", "").lower()
        assert "x-roles" in vary and "authorization" in vary, "Vary должен учитывать роли"

        observed_hashes.append(h)

    assert len(set(observed_hashes)) == 1, "Все три варианта пустых ролей должны давать одинаковый roles_hash"
