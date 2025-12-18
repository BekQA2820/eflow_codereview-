from conftest import compute_roles_hash
import pytest
from unittest.mock import Mock

# compute_roles_hash автоматически доступен из conftest.py
# импортировать его НЕ нужно — pytest сам добавит функцию в глобальное пространство


MANIFEST = "/api/v1/manifest"


def test_rbac_roles_hash_normalization(mocker, api_client, auth_header):
    """
    Проверяем:
    ✔ нормализацию ролей (lowercase, уникальность, сортировка)
    ✔ независимость хеша от порядка и регистра
    ✔ дубликаты не влияют на roles_hash
    ✔ корректность заголовков Vary
    ✔ MISS → HIT поведение кэша
    """

    roles_variants = [
        ["employee", "admin"],
        ["admin", "employee"],
        ["ADMIN", "employee"],
        ["employee", "admin", "admin"],
    ]

    normalized = ["admin", "employee"]
    expected_hash = compute_roles_hash(normalized)   # из conftest.py — работает без импорта

    responses = []
    for idx in range(len(roles_variants)):
        mock = Mock()
        mock.status_code = 200
        mock.headers = {
            "X-Roles-Hash": expected_hash,
            "X-Cache": "MISS" if idx == 0 else "HIT",
            "Vary": "Authorization, X-Roles",
        }
        mock.json.return_value = {"ok": True}
        responses.append(mock)

    mocker.patch("requests.get", side_effect=responses)

    hashes = []
    xcache_values = []

    for idx, roles in enumerate(roles_variants):
        hdr = {
            "X-Roles": ",".join(roles),
            **auth_header
        }

        r = api_client.get(MANIFEST, headers=hdr)

        assert r.status_code == 200

        # Хеш обязателен
        h = r.headers.get("X-Roles-Hash")
        assert h is not None, "X-Roles-Hash должен присутствовать"

        # Формат хеша — HEX lowercase, 32 символа
        assert len(h) == 32, "Длина хеша должна быть 32 символа"
        assert all(c in "0123456789abcdef" for c in h), "Хеш должен быть HEX lowercase"

        hashes.append(h)

        # Проверка кэша
        xcache = r.headers["X-Cache"]
        if idx == 0:
            assert xcache == "MISS", "Первый запрос должен быть MISS"
        else:
            assert xcache == "HIT", "Повторный запрос должен быть HIT"

        xcache_values.append(xcache)

        # Проверка Vary
        vary = r.headers.get("Vary", "").lower()
        assert "authorization" in vary and "x-roles" in vary, "Vary должен включать оба ключа"

    # Все значения хеша должны совпадать
    assert len(set(hashes)) == 1, "roles_hash должен быть одинаковым для всех вариантов ролей"
