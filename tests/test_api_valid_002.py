def test_widget_denylist_fields(api_client, auth_header):
    """
    Проверка ответ Manifest НЕ содержит запрещённые поля: requiredRoles и internalFlags
    """

    resp = api_client.get("/api/v1/manifest", headers=auth_header)
    assert resp.status_code == 200

    data = resp.json()
    for w in data["widgets"]:
        assert "requiredRoles" not in w, "Forbidden field returned!"
        assert "internalFlags" not in w, "Internal field leaked!"
