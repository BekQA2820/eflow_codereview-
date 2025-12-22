import json
import gzip

MANIFEST_PATH = "/api/v1/manifest"
MAX_SIZE_BYTES = 512 * 1024


def test_manifest_size_limit_and_gzip(mocker, api_client):
    manifest = {
        "widgets": [
            {
                "id": f"widget-{i}",
                "type": "mfe",
                "position": {"row": i, "col": 0, "width": 1},
            }
            for i in range(50)
        ],
        "layout": {"rows": 50, "columns": 1, "gridType": "fixed"},
        "version": "1",
    }

    raw_json = json.dumps(manifest).encode()

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/json"}
    resp.content = raw_json
    resp.json.return_value = manifest

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(MANIFEST_PATH)

    assert r.status_code == 200
    assert len(r.content) <= MAX_SIZE_BYTES

    gzipped = gzip.compress(r.content)
    assert len(gzipped) <= len(r.content) * 0.8
