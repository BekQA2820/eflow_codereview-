MANIFEST_PATH = "/api/v1/manifest"

ALLOWED_TYPES = {"mfe", "link", "container", "empty"}


def test_widget_type_is_from_allowed_list(mocker, api_client):
    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/json"}
    resp.json.return_value = {
        "widgets": [
            {"id": "w1", "type": "mfe", "position": {"row": 0, "col": 0, "width": 1}},
            {"id": "w2", "type": "link", "position": {"row": 0, "col": 1, "width": 1}},
            {"id": "w3", "type": "container", "position": {"row": 1, "col": 0, "width": 2}},
        ]
    }

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(MANIFEST_PATH)
    assert r.status_code == 200
    assert r.headers["Content-Type"].startswith("application/json")

    data = r.json()
    assert "widgets" in data and isinstance(data["widgets"], list)

    for idx, w in enumerate(data["widgets"]):
        assert "type" in w, f"widget[{idx}] missing type"
        assert isinstance(w["type"], str), f"widget[{idx}].type must be string"
        assert w["type"] in ALLOWED_TYPES, f"widget[{idx}].type={w['type']} is not allowed"
