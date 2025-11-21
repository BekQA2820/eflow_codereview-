MANIFEST = "/api/v1/manifest"


def test_rbac_role_normalization(api_client, auth_header_factory):
    # Роли в разном порядке + регистр
    h1 = auth_header_factory(["employee", "admin"])
    h2 = auth_header_factory(["ADMIN", "employee"])  # Должно считаться тем же набором

    r1 = api_client.get(MANIFEST, headers=h1)
    assert r1.status_code == 200
    assert r1.headers.get("X-Cache") == "MISS"

    r2 = api_client.get(MANIFEST, headers=h2)
    assert r2.status_code == 200

    # Должен быть HIT — ключ кэша идентичен
    assert r2.headers.get("X-Cache") == "HIT"
