import json

MANIFEST_PATH = "/api/v1/manifest"


def test_all_widget_ids_are_unique(mocker, api_client):
    """
    API CONTRACT 024
    Все widget.id должны быть уникальными
    """

    manifest = {
        "layout": {"rows": 1, "columns": 3, "gridType": "fixed"},
        "widgets": [
            {
                "id": "widget-a",
                "type": "mfe",
                "visible": True,
                "position": {"row": 0, "col": 0, "width": 1},
            },
            {
                "id": "widget-b",
                "type": "link",
                "visible": True,
                "position": {"row": 0, "col": 1, "width": 1},
            },
            {
                "id": "widget-c",
                "type": "empty",
                "visible": True,
                "position": {"row": 0, "col": 2, "width": 1},
            },
        ],
        "version": "1.0",
    }

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/json"}
    resp.json.return_value = manifest
    resp.text = json.dumps(manifest)

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(MANIFEST_PATH)

    assert r.status_code == 200
    widgets = r.json()["widgets"]

    ids = [w["id"] for w in widgets]

    assert all(isinstance(i, str) and i.strip() for i in ids)
    assert len(ids) == len(set(ids)), f"Обнаружены дубликаты widget.id: {ids}"
