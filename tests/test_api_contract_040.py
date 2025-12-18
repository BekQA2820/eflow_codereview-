MANIFEST_PATH = "/api/v1/manifest"


def test_additional_widget_fields_not_null(mocker, api_client):
    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/json"}
    resp.json.return_value = {
        "widgets": [
            {
                "id": "w-title",
                "type": "mfe",
                "visible": True,
                "title": "Dashboard",
                "description": "Main widget",
                "mfe": "https://cdn.example.com/app",
                "position": {"row": 0, "col": 0, "width": 1},
            }
        ],
        "layout": {"rows": 1, "columns": 1, "gridType": "fixed"},
        "version": "1",
    }

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(MANIFEST_PATH)
    data = r.json()

    for w in data["widgets"]:
        for field in ("title", "description"):
            if field in w:
                assert w[field] is not None, f"{field} не должен быть null"
                assert not isinstance(w[field], dict), f"{field} не должен быть объектом"
