MANIFEST = "/api/v1/manifest"


def test_rbac_subset_filtering(api_client, employee_token, admin_token):
    # roles: ["employee"] → НЕ должен видеть admin-виджет
    r1 = api_client.get(MANIFEST, headers={"Authorization": employee_token})
    widgets1 = r1.json().get("widgets", [])

    # roles: ["employee", "admin"] → должен видеть
    r2 = api_client.get(MANIFEST, headers={"Authorization": admin_token})
    widgets2 = r2.json().get("widgets", [])

    admin_widgets = [w for w in widgets2 if w.get("id") == "admin_widget"]

    assert len(admin_widgets) > 0
    assert all(w.get("id") != "admin_widget" for w in widgets1)
