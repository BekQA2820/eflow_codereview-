import json

MANIFEST_PATH = "/api/v1/manifest"


def test_manifest_stable_under_high_load(mocker, api_client):
    manifest = {
        "widgets": [
            {
                "id": "widget-stable",
                "type": "mfe",
                "position": {"row": 0, "col": 0, "width": 1},
            }
        ],
        "layout": {"rows": 1, "columns": 1, "gridType": "fixed"},
        "version": "1",
    }

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/json"}
    resp.json.return_value = manifest
    resp.content = json.dumps(manifest).encode("utf-8")

    mocker.patch("requests.get", return_value=resp)

    results = []

    for _ in range(30):
        r = api_client.get(MANIFEST_PATH)
        assert r.status_code == 200
        results.append(r.json())

    first = results[0]

    for item in results[1:]:
        assert item == first
