MANIFEST_PATH = "/api/v1/manifest"

ALLOWED_TYPES = {"mfe", "link", "container", "empty"}


def test_api_contract_widget_types(api_client, auth_header):
    r = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r.status_code == 200

    widgets = r.json().get("widgets", [])

    for w in widgets:
        assert "type" in w, f"У виджета {w} отсутствует поле type"
        assert w["type"] in ALLOWED_TYPES, f"Некорректный widget.type: {w['type']}"
