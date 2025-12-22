import json
import pytest

MANIFEST_PATH = "/api/v1/manifest"


def test_manifest_is_stable_between_identical_requests(mocker, api_client):
    manifest = {
        "widgets": [
            {"id": "a", "type": "mfe", "position": {"row": 0, "col": 0, "width": 1}}
        ],
        "layout": {"rows": 1, "columns": 1, "gridType": "fixed"},
        "version": "1",
        "generatedAt": "2025-01-01T00:00:00.000Z",
    }

    def make_resp():
        r = mocker.Mock()
        r.status_code = 200
        r.headers = {"Content-Type": "application/json"}
        r.json.return_value = manifest
        r.text = json.dumps(manifest)
        return r

    mocker.patch("requests.get", side_effect=[make_resp(), make_resp(), make_resp()])

    r1 = api_client.get(MANIFEST_PATH).json()
    r2 = api_client.get(MANIFEST_PATH).json()
    r3 = api_client.get(MANIFEST_PATH).json()

    for key in r1:
        if key != "generatedAt":
            assert r1[key] == r2[key] == r3[key]
