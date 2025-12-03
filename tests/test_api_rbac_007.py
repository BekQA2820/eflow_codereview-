MANIFEST_PATH = "/api/v1/manifest"


def test_api_rbac_public_widget_no_required_roles(api_client, auth_header):
    """
    GET /manifest с разными ролями.
    Public-виджеты должны быть одинаковыми.
    """
    headers_a = auth_header.copy()
    headers_a["X-Roles"] = "employee"

    headers_b = auth_header.copy()
    headers_b["X-Roles"] = "manager"

    r1 = api_client.get(MANIFEST_PATH, headers=headers_a)
    r2 = api_client.get(MANIFEST_PATH, headers=headers_b)

    assert r1.status_code == 200
    assert r2.status_code == 200

    w1 = r1.json().get("widgets", [])
    w2 = r2.json().get("widgets", [])

    pub1 = [w for w in w1 if not w.get("requiredRoles")]
    pub2 = [w for w in w2 if not w.get("requiredRoles")]

    assert pub1 == pub2
