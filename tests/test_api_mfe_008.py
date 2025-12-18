import requests


def test_mfe_remote_entry_cache_control():
    url = "https://cdn.example.com/app1/remoteEntry.js"

    resp = requests.head(url)

    cache_control = resp.headers.get("Cache-Control", "").lower()

    assert resp.status_code == 200
    assert "max-age" in cache_control
    assert "no-store" not in cache_control
    assert "no-cache" not in cache_control
    assert "private" not in cache_control
    assert "etag" in resp.headers
