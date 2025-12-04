MANIFEST_PATH = "/api/v1/manifest"


def test_api_rbac_roles_hash_empty_roles(api_client, auth_header):
    variants = [None, "", None]
    hashes = []

    for roles in variants:
        headers = auth_header.copy()
        if roles is not None:
            headers["X-Roles"] = roles

        r = api_client.get(MANIFEST_PATH, headers=headers)
        assert r.status_code == 200

        hashes.append(r.headers.get("X-Roles-Hash"))

    assert len(set(hashes)) == 1
