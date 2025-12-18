import re


MANIFEST_PATH = "/api/v1/manifest"


def test_mfe_urls_contain_version_or_hash(mocker, api_client):
    manifest = {
        "widgets": [
            {
                "id": "mfe-v1",
                "type": "mfe",
                "mfe": "https://cdn.example.com/app/v1",
                "position": {"row": 0, "col": 0, "width": 2},
            },
            {
                "id": "mfe-hash",
                "type": "mfe",
                "mfe": "https://cdn.example.com/app?version=abc123",
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

    for widget in r.json()["widgets"]:
        url = widget["mfe"]

        has_path_version = re.search(r"/v\d+", url)
        has_query_version = re.search(r"(version|v)=", url)

        assert has_path_version or has_query_version, (
            f"MFE URL не содержит версии или хеша: {url}"
        )
