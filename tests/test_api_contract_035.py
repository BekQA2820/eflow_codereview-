MANIFEST_PATH = "/api/v1/manifest"


def test_widget_visible_is_strict_boolean(mocker, api_client):
    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/json"}
    resp.json.return_value = {
        "widgets": [
            {
                "id": "w-visible-true",
                "type": "mfe",
                "visible": True,
                "mfe": "https://cdn.example.com/app",
                "position": {"row": 0, "col": 0, "width": 1},
            },
            {
                "id": "w-visible-false",
                "type": "link",
                "visible": False,
                "position": {"row": 0, "col": 1, "width": 1},
            },
        ],
        "layout": {"rows": 1, "columns": 2, "gridType": "fixed"},
        "version": "1",
    }

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(MANIFEST_PATH)
    data = r.json()

    for idx, w in enumerate(data["widgets"]):
        assert "visible" in w
        assert isinstance(
            w["visible"], bool
        ), f"widget[{idx}].visible должен быть boolean"
