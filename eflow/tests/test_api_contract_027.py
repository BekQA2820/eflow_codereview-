import json

MANIFEST_PATH = "/api/v1/manifest"


def test_widget_position_has_strict_structure(mocker, api_client):
    """
    API CONTRACT 027
    position содержит только row, col, width
    """

    manifest = {
        "layout": {"rows": 1, "columns": 4, "gridType": "fixed"},
        "widgets": [
            {
                "id": "widget-1",
                "type": "mfe",
                "visible": True,
                "position": {"row": 0, "col": 0, "width": 2},
            }
        ],
        "version": "1",
    }

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/json"}
    resp.json.return_value = manifest
    resp.text = json.dumps(manifest)

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(MANIFEST_PATH)
    data = r.json()

    layout_columns = data["layout"]["columns"]

    for w in data["widgets"]:
        pos = w["position"]

        assert set(pos.keys()) == {"row", "col", "width"}

        assert isinstance(pos["row"], int)
        assert isinstance(pos["col"], int)
        assert isinstance(pos["width"], int)

        assert pos["row"] >= 0
        assert pos["col"] >= 0
        assert pos["width"] >= 1

        assert pos["col"] + pos["width"] <= layout_columns
