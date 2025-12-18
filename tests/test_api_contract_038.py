MANIFEST_PATH = "/api/v1/manifest"

ALLOWED_CONTAINER_FIELDS = {
    "id",
    "type",
    "visible",
    "position",
    "widgets",
}


def test_container_widget_structure_is_valid(mocker, api_client):
    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/json"}
    resp.json.return_value = {
        "widgets": [
            {
                "id": "container-1",
                "type": "container",
                "visible": True,
                "position": {"row": 0, "col": 0, "width": 3},
                "widgets": [
                    {
                        "id": "child-1",
                        "type": "mfe",
                        "visible": True,
                        "mfe": "https://cdn.example.com/child",
                        "position": {"row": 0, "col": 0, "width": 1},
                    }
                ],
            }
        ],
        "layout": {"rows": 1, "columns": 3, "gridType": "fixed"},
        "version": "1",
    }

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(MANIFEST_PATH)
    data = r.json()

    for w in data["widgets"]:
        if w.get("type") != "container":
            continue

        extra_fields = set(w.keys()) - ALLOWED_CONTAINER_FIELDS
        assert not extra_fields, f"container содержит лишние поля: {extra_fields}"

        pos = w.get("position")
        assert isinstance(pos, dict)
        assert set(pos.keys()) == {"row", "col", "width"}
        assert all(isinstance(pos[k], int) for k in pos)
