import re
from urllib.parse import urlparse


MANIFEST_PATH = "/api/v1/manifest"


def test_widget_mfe_urls_are_valid_and_safe(mocker, api_client):
    manifest = {
        "widgets": [
            {
                "id": "mfe-1",
                "type": "mfe",
                "mfe": "https://cdn.example.com/app1",
                "position": {"row": 0, "col": 0, "width": 2},
            },
            {
                "id": "mfe-2",
                "type": "mfe",
                "mfe": "https://cdn.example.com/app2?v=1",
                "position": {"row": 1, "col": 0, "width": 2},
            },
        ],
        "layout": {"rows": 2, "columns": 2, "gridType": "fixed"},
        "version": "1",
    }

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/json"}
    resp.json.return_value = manifest

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(MANIFEST_PATH)
    widgets = r.json()["widgets"]

    for widget in widgets:
        url = widget["mfe"]

        parsed = urlparse(url)
        assert parsed.scheme == "https"
        assert parsed.netloc

        forbidden = ("javascript:", "data:", "file:", "blob:")
        assert not any(url.lower().startswith(f) for f in forbidden)

        assert "<" not in url
        assert ">" not in url
        assert not re.search(r"\s", url)
