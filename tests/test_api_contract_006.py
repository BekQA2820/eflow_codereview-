import re

MANIFEST_PATH = "/api/v1/manifest"

ID_PATTERN = r"^[a-z0-9][a-z0-9\-_:]*[a-z0-9]$"  # kebab-case + безопасные символы


def test_api_contract_widget_id_format_and_uniqueness(api_client, auth_header):
    r = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r.status_code == 200

    widgets = r.json().get("widgets", [])
    ids = []

    for w in widgets:
        assert "id" in w, f"Виджет {w} не содержит id"

        wid = w["id"]
        ids.append(wid)

        assert re.match(ID_PATTERN, wid), f"Некорректный формат widget.id: {wid}"

    assert len(ids) == len(set(ids)), "widget.id должны быть уникальны"
