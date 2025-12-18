MANIFEST_PATH = "/api/v1/manifest"


def test_no_invalid_vertical_overlap(mocker, api_client):
    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/json"}
    resp.json.return_value = {
        "widgets": [
            {"id": "top", "type": "mfe", "visible": True, "position": {"row": 0, "col": 0, "width": 2}},
            {"id": "bottom", "type": "mfe", "visible": True, "position": {"row": 1, "col": 0, "width": 2}},
        ],
        "layout": {"rows": 2, "columns": 2, "gridType": "fixed"},
        "version": "1",
    }

    mocker.patch("requests.get", return_value=resp)

    widgets = api_client.get(MANIFEST_PATH).json()["widgets"]

    for i, w1 in enumerate(widgets):
        p1 = w1["position"]
        for j, w2 in enumerate(widgets):
            if i == j:
                continue
            p2 = w2["position"]

            horizontal_overlap = not (
                p1["col"] + p1["width"] <= p2["col"]
                or p2["col"] + p2["width"] <= p1["col"]
            )

            if horizontal_overlap:
                assert p1["row"] != p2["row"], "вертикальное пересечение при одинаковом row"
