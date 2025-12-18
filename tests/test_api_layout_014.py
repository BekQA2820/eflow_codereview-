MANIFEST_PATH = "/api/v1/manifest"


def test_no_horizontal_overlap_with_large_width(mocker, api_client):
    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/json"}
    resp.json.return_value = {
        "widgets": [
            {"id": "w1", "type": "mfe", "visible": True, "position": {"row": 0, "col": 0, "width": 3}},
            {"id": "w2", "type": "mfe", "visible": True, "position": {"row": 0, "col": 3, "width": 2}},
        ],
        "layout": {"rows": 1, "columns": 5, "gridType": "fixed"},
        "version": "1",
    }

    mocker.patch("requests.get", return_value=resp)

    widgets = api_client.get(MANIFEST_PATH).json()["widgets"]

    ranges = []
    for w in widgets:
        pos = w["position"]
        ranges.append((pos["col"], pos["col"] + pos["width"]))

    for i, (a_start, a_end) in enumerate(ranges):
        for j, (b_start, b_end) in enumerate(ranges):
            if i == j:
                continue
            assert not (a_start < b_end and b_start < a_end), "горизонтальное пересечение виджетов"
