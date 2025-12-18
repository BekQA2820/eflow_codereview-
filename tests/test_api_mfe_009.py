import requests


def test_mfe_remote_entry_cors_headers():
    url = "https://cdn.example.com/app1/remoteEntry.js"

    resp = requests.head(url)

    assert resp.status_code == 200

    assert "Access-Control-Allow-Origin" in resp.headers
    assert resp.headers["Access-Control-Allow-Origin"] not in ("", None)

    assert "Access-Control-Allow-Methods" in resp.headers

    raw_headers = str(resp.headers).lower()
    assert "<html" not in raw_headers
