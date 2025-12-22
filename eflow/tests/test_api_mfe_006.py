import urllib.parse

MANIFEST_PATH = "/api/v1/manifest"


def test_mfe_urls_are_https_and_safe(mocker, api_client):
    manifest = {
        "widgets": [
            {
                "id": "mfe1",
                "type": "mfe",
                "mfe": "https://cdn.example.com/app/v1",
                "position": {"row": 0, "col": 0, "width": 1},
            }
        ],
        "layout": {"rows": 1, "columns": 1, "gridType": "fixed"},
    }

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/json"}
    resp.json.return_value = manifest

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(MANIFEST_PATH)

    for w in r.json()["widgets"]:
        url = w.get("mfe")
        parsed = urllib.parse.urlparse(url)

        assert parsed.scheme == "https"
        assert not url.startswith(("javascript:", "data:", "file:", "blob:"))
        assert "<" not in url and ">" not in url
