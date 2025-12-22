MANIFEST_PATH = "/api/v1/manifest"


def test_all_mfe_urls_are_unique(mocker, api_client):
    manifest = {
        "widgets": [
            {
                "id": "mfe-a",
                "type": "mfe",
                "mfe": "https://cdn.example.com/appA",
                "position": {"row": 0, "col": 0, "width": 1},
            },
            {
                "id": "mfe-b",
                "type": "mfe",
                "mfe": "https://cdn.example.com/appB",
                "position": {"row": 0, "col": 1, "width": 1},
            },
        ],
        "layout": {"rows": 1, "columns": 2, "gridType": "fixed"},
        "version": "1",
    }

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/json"}
    resp.json.return_value = manifest

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(MANIFEST_PATH)

    mfe_urls = [
        w["mfe"]
        for w in r.json()["widgets"]
        if w.get("type") == "mfe"
    ]

    assert len(mfe_urls) == len(set(mfe_urls)), "Найдены дублирующиеся MFE URL"
