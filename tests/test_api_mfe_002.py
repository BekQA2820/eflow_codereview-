import requests

MANIFEST_PATH = "/api/v1/manifest"


def test_api_mfe_remote_entry_available(api_client, auth_header):
    r = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r.status_code == 200

    widgets = r.json().get("widgets", [])

    for w in widgets:
        mfe_url = w.get("mfe") or w.get("mfeUrl") or w.get("url")
        if not mfe_url:
            continue  # не MFE-виджет

        # Чаще всего remoteEntry.js — это URL вида <mfe_url>/remoteEntry.js
        if not mfe_url.endswith("remoteEntry.js"):
            mfe_url = mfe_url.rstrip("/") + "/remoteEntry.js"

        resp = requests.head(mfe_url, timeout=5)
        assert resp.status_code == 200, f"remoteEntry.js недоступен: {mfe_url}"
