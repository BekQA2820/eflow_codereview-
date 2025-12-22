MANIFEST_PATH = "/api/v1/manifest"


def test_layout_rows_matches_content(mocker, api_client):
    manifest = {
        "widgets": [
            {"id": "w1", "type": "mfe", "position": {"row": 0, "col": 0, "width": 1}},
            {"id": "w2", "type": "mfe", "position": {"row": 2, "col": 0, "width": 1}},
        ],
        "layout": {"rows": 3, "columns": 1, "gridType": "fixed"},
    }

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/json"}
    resp.json.return_value = manifest

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(MANIFEST_PATH)
    data = r.json()

    max_row = max(w["position"]["row"] for w in data["widgets"])
    assert data["layout"]["rows"] >= max_row + 1
