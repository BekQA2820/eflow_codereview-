MANIFEST_PATH = "/api/v1/manifest"


def test_col_plus_width_not_exceed_columns(mocker, api_client):
    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/json"}
    resp.json.return_value = {
        "widgets": [
            {"id": "w1", "type": "mfe", "visible": True, "position": {"row": 0, "col": 0, "width": 2}},
            {"id": "w2", "type": "mfe", "visible": True, "position": {"row": 0, "col": 2, "width": 1}},
        ],
        "layout": {"rows": 1, "columns": 3, "gridType": "fixed"},
        "version": "1",
    }

    mocker.patch("requests.get", return_value=resp)

    data = api_client.get(MANIFEST_PATH).json()
    columns = data["layout"]["columns"]

    for w in data["widgets"]:
        pos = w["position"]
        assert pos["col"] + pos["width"] <= columns, (
            f"widget {w['id']} выходит за пределы columns"
        )
