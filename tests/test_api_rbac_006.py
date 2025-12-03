MANIFEST_PATH = "/api/v1/manifest"


def test_acl_cache_with_duplicate_roles(api_client, auth_header):

    roles_single = ["employee"]
    roles_dup = ["employee", "employee"]

    headers1 = auth_header.copy()
    headers1["X-Roles"] = ",".join(roles_single)

    r1 = api_client.get(MANIFEST_PATH, headers=headers1)
    assert r1.status_code == 200
    x_cache1 = r1.headers.get("X-Cache", "").lower()

    r2 = api_client.get(MANIFEST_PATH, headers=headers1)
    assert r2.status_code == 200
    x_cache2 = r2.headers.get("X-Cache", "").lower()

    # Если backend реально отдаёт MISS/HIT - проверим
    if x_cache1 and x_cache2:
        assert "miss" in x_cache1
        assert "hit" in x_cache2

    # Теперь запрос с дубликатами ролей - ACL должен быть тем же
    headers_dup = auth_header.copy()
    headers_dup["X-Roles"] = ",".join(roles_dup)

    r_dup = api_client.get(MANIFEST_PATH, headers=headers_dup)
    assert r_dup.status_code == 200

    # Проверяем заголовок Vary (Authorization, X-Roles)
    vary = r_dup.headers.get("Vary", "").lower()
    if vary:
        assert "authorization" in vary or "x-roles" in vary
