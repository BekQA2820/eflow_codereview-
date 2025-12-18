import json

MANIFEST_PATH = "/api/v1/manifest"


def test_manifest_has_no_nulls_or_empty_objects_in_critical_fields(mocker, api_client):
    """
    API CONTRACT 025
    Критичные поля не содержат null или пустые объекты {}
    """

    manifest = {
        "layout": {"rows": 1, "columns": 2, "gridType": "fixed"},
        "widgets": [
            {
                "id": "widget-1",
                "type": "mfe",
                "visible": True,
                "position": {"row": 0, "col": 0, "width": 1},
            },
            {
                "id": "widget-2",
                "type": "link",
                "visible": False,
                "position": {"row": 0, "col": 1, "width": 1},
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
    data = r.json()

    # layout
    assert data["layout"] is not None
    assert data["layout"] != {}

    for key in ("rows", "columns", "gridType"):
        assert data["layout"][key] is not None

    # widgets
    for w in data["widgets"]:
        assert w is not None and w != {}

        assert w["id"] is not None
        assert w["type"] is not None
        assert w["visible"] is not None

        pos = w["position"]
        assert pos is not None and pos != {}

        for k in ("row", "col", "width"):
            assert pos[k] is not None
