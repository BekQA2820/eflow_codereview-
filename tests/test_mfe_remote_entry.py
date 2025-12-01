import requests

MANIFEST = "/api/v1/manifest"


def test_mfe_remote_entry_urls(api_client, auth_header):
    r = api_client.get(MANIFEST, headers=auth_header)
    widgets = r.json().get("widgets", [])

    for w in widgets:
        mfe_url = w.get("mfe")
        assert mfe_url.startswith("http"), "mfe должен быть валидным URL"

        # HEAD request для проверки доступности
        resp = requests.head(mfe_url, timeout=5)
        assert resp.status_code in (200, 204)
