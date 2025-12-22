import requests

MANIFEST_PATH = "/api/v1/manifest"

def test_api_mfe_remote_entry(api_client, auth_header):
    """
    Проверяет валидность MFE URL (remoteEntry.js):
     корректный URL
     отвечает HEAD
     нет 404
    """
    r = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r.status_code == 200

    data = r.json()

    for widget in data["widgets"]:
        mfe_url = widget.get("mfe")
        assert mfe_url, "mfe обязателен"

        # HEAD запрос к файлу
        head = requests.head(mfe_url, timeout=5)
        assert head.status_code == 200, f"MFE недоступен: {mfe_url}"
        assert "javascript" in head.headers.get("Content-Type", "").lower()
