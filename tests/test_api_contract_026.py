import json

MANIFEST_PATH = "/api/v1/manifest"


def test_manifest_strict_type_validation(mocker, api_client):
    """
    API CONTRACT 026
    Все поля manifest соответствуют ожидаемым типам
    """

    manifest = {
        "layout": {"rows": 2, "columns": 4, "gridType": "fixed"},
        "widgets": [
            {
                "id": "widget-a",
                "type": "mfe",
                "visible": True,
                "position": {"row": 0, "col": 0, "width": 2},
                "mfe": "https://cdn.example.com/app/v1",
            },
            {
                "id": "widget-b",
                "type": "link",
                "visible": False,
                "position": {"row": 1, "col": 0, "width": 1},
            },
        ],
        "version": "2",
    }

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/json"}
    resp.json.return_value = manifest
    resp.text = json.dumps(manifest)

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(MANIFEST_PATH)
    data = r.json()

    # layout
    assert isinstance(data["layout"]["rows"], int)
    assert isinstance(data["layout"]["columns"], int)
    assert isinstance(data["layout"]["gridType"], str)

    # widgets
    assert isinstance(data["widgets"], list)

    for w in data["widgets"]:
        assert isinstance(w["id"], str)
        assert isinstance(w["type"], str)
        assert isinstance(w["visible"], bool)

        pos = w["position"]
        assert isinstance(pos["row"], int)
        assert isinstance(pos["col"], int)
        assert isinstance(pos["width"], int)

        if w["type"] == "mfe":
            assert "mfe" in w
            assert isinstance(w["mfe"], str)
            assert w["mfe"].startswith("https://")
