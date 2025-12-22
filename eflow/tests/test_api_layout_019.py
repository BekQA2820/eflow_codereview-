MANIFEST_PATH = "/api/v1/manifest"


def test_single_position_per_widget_id(mocker, api_client):
    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/json"}
    resp.json.return_value = {
        "widgets": [
            {"id": "w1", "type": "mfe", "visible": True, "position": {"row": 0, "col": 0, "width": 1}},
            {"id": "w2", "type": "mfe", "visible": True, "position": {"row": 0, "col": 1, "width": 1}},
        ],
        "layout": {"rows": 1, "columns": 2, "gridType": "fixed"},
        "version": "1",
    }

    mocker.patch("requests.get", return_value=resp)

    widgets = api_client.get(MANIFEST_PATH).json()["widgets"]

    seen = {}
    for w in widgets:
        wid = w["id"]
        pos = tuple(w["position"].values())
        if wid in seen:
            assert seen[wid] == pos, f"widget.id {wid} имеет несколько разных позиций"
        else:
            seen[wid] = pos
