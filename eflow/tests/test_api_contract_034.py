MANIFEST_PATH = "/api/v1/manifest"


def test_widget_must_have_required_fields(mocker, api_client):
    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/json"}
    resp.json.return_value = {
        "widgets": [
            {
                "id": "w1",
                "type": "mfe",
                "visible": True,
                "mfe": "https://cdn.example.com/app",
                "position": {"row": 0, "col": 0, "width": 2},
            },
            {
                "id": "w2",
                "type": "link",
                "visible": False,
                "position": {"row": 1, "col": 0, "width": 1},
            },
        ],
        "layout": {"rows": 2, "columns": 2, "gridType": "fixed"},
        "version": "1",
    }

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(MANIFEST_PATH)
    data = r.json()

    for idx, w in enumerate(data["widgets"]):
        for field in ("id", "type", "position", "visible"):
            assert field in w, f"widget[{idx}] missing {field}"
            assert w[field] is not None

        assert isinstance(w["visible"], bool)
        assert isinstance(w["position"], dict)
        assert w["position"]

        if w["type"] == "mfe":
            assert "mfe" in w
            assert isinstance(w["mfe"], str)
