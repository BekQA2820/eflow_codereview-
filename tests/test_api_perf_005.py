import json
import gzip

MANIFEST_PATH = "/api/v1/manifest"


def test_manifest_gzip_compression(mocker, api_client):
    manifest = {
        "widgets": [
            {
                "id": "widget-1",
                "type": "mfe",
                "position": {"row": 0, "col": 0, "width": 1},
            }
        ],
        "layout": {"rows": 1, "columns": 1, "gridType": "fixed"},
        "version": "1",
    }

    raw = json.dumps(manifest).encode("utf-8")
    gzipped = gzip.compress(raw)

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {
        "Content-Type": "application/json",
        "Content-Encoding": "gzip",
    }
    resp.content = gzipped

    def json_loader():
        return json.loads(gzip.decompress(resp.content).decode("utf-8"))

    resp.json.side_effect = json_loader

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(
        MANIFEST_PATH,
        headers={"Accept-Encoding": "gzip"},
    )

    assert r.status_code == 200
    assert r.headers.get("Content-Encoding") == "gzip"

    data = r.json()
    assert isinstance(data, dict)
    assert "widgets" in data
