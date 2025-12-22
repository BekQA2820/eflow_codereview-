

MANIFEST_PATH = "/api/v1/manifest"


def test_widgets_sorted_by_col_within_each_row(mocker, api_client):

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/json"}
    resp.json.return_value = {
        "widgets": [
            {"id": "a", "position": {"row": 0, "col": 0, "width": 1}},
            {"id": "c", "position": {"row": 0, "col": 1, "width": 1}},
            {"id": "b", "position": {"row": 0, "col": 2, "width": 1}},
        ],
        "layout": {"rows": 1, "columns": 3, "gridType": "fixed"},
        "version": "1",
    }

    mocker.patch("requests.get", return_value=resp)

    widgets = api_client.get(MANIFEST_PATH).json()["widgets"]

    rows = {}
    for w in widgets:
        row = w["position"]["row"]
        rows.setdefault(row, []).append(w)

    for row_widgets in rows.values():
        cols = [w["position"]["col"] for w in row_widgets]
        assert cols == sorted(cols), "виджеты внутри одной строки должны быть отсортированы по col"
