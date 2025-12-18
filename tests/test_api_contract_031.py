from urllib.parse import urlparse

MANIFEST_PATH = "/api/v1/manifest"

FORBIDDEN_SCHEMES = {"javascript", "data", "file", "blob", "vbscript"}


def test_link_widget_url_is_safe(mocker, api_client):
    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/json"}
    resp.json.return_value = {
        "widgets": [
            {
                "id": "link-1",
                "type": "link",
                "url": "https://example.com/page",
                "position": {"row": 0, "col": 0, "width": 2},
            }
        ]
    }

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(MANIFEST_PATH)
    data = r.json()

    for idx, w in enumerate(data["widgets"]):
        if w.get("type") != "link":
            continue

        assert "url" in w, f"widget[{idx}] link must contain url"
        url = w["url"]
        assert isinstance(url, str)
        assert "<" not in url and ">" not in url

        parsed = urlparse(url)
        assert parsed.scheme == "https", f"widget[{idx}] url must use https"
        assert parsed.scheme not in FORBIDDEN_SCHEMES
        assert parsed.netloc, f"widget[{idx}] url must have host"
