MANIFEST_PATH = "/api/v1/manifest"


def test_widgets_sorted_by_specified_algorithm(mocker, api_client):
    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/json"}
    resp.json.return_value = {
    "widgets": [
        {"id": "a-widget", "type": "mfe", "visible": True, "position": {"row": 0, "col": 0, "width": 1}},
        {"id": "b-widget", "type": "mfe", "visible": True, "position": {"row": 0, "col": 1, "width": 1}},
    ],
    "layout": {"rows": 1, "columns": 2, "gridType": "fixed"},
    "version": "1",
}

    mocker.patch("requests.get", return_value=resp)

    widgets = api_client.get(MANIFEST_PATH).json()["widgets"]
    ids = [w["id"] for w in widgets]

    assert ids == sorted(ids), "порядок виджетов не соответствует алгоритму сортировки"
