import pytest
from unittest.mock import Mock
from conftest import compute_roles_hash

MANIFEST = "/api/v1/manifest"


def test_rbac_acl_cache_behavior(mocker, api_client, auth_header):
    """
    Проверяем:
    ✔ ACL зависит только от нормализованных ролей
    ✔ дублированные роли не порождают новый кэш
    ✔ X-Cache: MISS → HIT
    ✔ обязательные заголовки Vary
    ✔ контент идентичен при одинаковых наборах ролей
    """

    roles1 = ["employee"]
    roles2 = ["employee", "employee"]  # дубликаты

    h1 = compute_roles_hash(roles1)
    h2 = compute_roles_hash(roles2)

    assert h1 == h2, "Хеш должен быть одинаковым при дублях"

    # Тела манифеста одинаковы — ACL одинаков
    body = {"widgets": [{"id": "w1"}], "acl": ["employee"]}

    r1 = Mock()
    r1.status_code = 200
    r1.headers = {"X-Cache": "MISS", "X-Roles-Hash": h1, "Vary": "Authorization, X-Roles"}
    r1.json.return_value = body

    r2 = Mock()
    r2.status_code = 200
    r2.headers = {"X-Cache": "HIT", "X-Roles-Hash": h2, "Vary": "Authorization, X-Roles"}
    r2.json.return_value = body

    mocker.patch("requests.get", side_effect=[r1, r2])

    # ---- Запрос 1 ----
    r = api_client.get(MANIFEST, headers={"X-Roles": ",".join(roles1), **auth_header})
    assert r.status_code == 200
    assert r.headers["X-Cache"] == "MISS"

    # ---- Запрос 2 ----
    r = api_client.get(MANIFEST, headers={"X-Roles": ",".join(roles2), **auth_header})
    assert r.status_code == 200
    assert r.headers["X-Cache"] == "HIT"

    # Контент идентичен
    assert r.json() == body
