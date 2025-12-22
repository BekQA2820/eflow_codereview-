import re


MANIFEST_PATH = "/api/v1/manifest"


def test_all_mfe_urls_use_same_version_format(mocker, api_client):
    manifest = {
        "widgets": [
            {
                "id": "mfe-1",
                "type": "mfe",
                "mfe": "https://cdn.example.com/app/v1",
                "position": {"row": 0, "col": 0, "width": 2},
            },
            {
                "id": "mfe-2",
                "type": "mfe",
                "mfe": "https://cdn.example.com/other/v1",
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

    versions = set()

    for widget in r.json()["widgets"]:
        url = widget["mfe"]
        match = re.search(r"/v(\d+)", url)
        assert match, f"В MFE URL отсутствует версия: {url}"
        versions.add(match.group(0))

    assert len(versions) == 1, f"Используются разные версии MFE URL: {versions}"
