MANIFEST_PATH = "/api/v1/manifest"


def test_layout_compacted_after_rbac_filtering(mocker, api_client):
    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/json"}
    resp.json.return_value = {
        "widgets": [
            {"id": "public", "type": "mfe", "visible": True, "position": {"row": 0, "col": 0, "width": 1}},
            {"id": "public2", "type": "mfe", "visible": True, "position": {"row": 0, "col": 1, "width": 1}},
        ],
        "layout": {"rows": 1, "columns": 2, "gridType": "fixed"},
        "version": "1",
    }

    mocker.patch("requests.get", return_value=resp)

    widgets = api_client.get(MANIFEST_PATH).json()["widgets"]

    cols = [w["position"]["col"] for w in widgets]
    cols_sorted = sorted(cols)

    for idx, col in enumerate(cols_sorted):
        assert col == idx, "обнаружена дыра в layout после фильтрации"
