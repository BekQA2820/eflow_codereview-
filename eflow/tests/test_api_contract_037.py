MANIFEST_PATH = "/api/v1/manifest"


def test_manifest_has_no_empty_objects(mocker, api_client):
    manifest = {
        "widgets": [
            {
                "id": "w1",
                "type": "mfe",
                "visible": True,
                "position": {"row": 0, "col": 0, "width": 1},
            }
        ],
        "layout": {"rows": 1, "columns": 1, "gridType": "fixed"},
    }

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/json"}
    resp.json.return_value = manifest

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(MANIFEST_PATH)
    data = r.json()

    def walk(obj):
        if isinstance(obj, dict):
            assert obj != {}
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for i in obj:
                walk(i)

    walk(data)
