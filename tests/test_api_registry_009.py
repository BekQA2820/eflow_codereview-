import json

MANIFEST_PATH = "/api/v1/manifest"


def test_registry_semantic_error_uses_fallback(mocker, api_client):
    valid_manifest = {
        "widgets": [
            {"id": "w1", "type": "mfe", "visible": True, "position": {"row": 0, "col": 0, "width": 1}}
        ],
        "layout": {"rows": 1, "columns": 1, "gridType": "fixed"},
        "version": "10",
    }

    fallback_resp = mocker.Mock()
    fallback_resp.status_code = 200
    fallback_resp.headers = {
        "Content-Type": "application/json",
        "X-Cache": "HIT (registry fallback)",
    }
    fallback_resp.json.return_value = valid_manifest
    fallback_resp.content = json.dumps(valid_manifest).encode()

    mocker.patch("requests.get", return_value=fallback_resp)

    r = api_client.get(MANIFEST_PATH)

    assert r.status_code == 200
    assert "fallback" in r.headers.get("X-Cache", "").lower()
    assert r.json() == valid_manifest

    raw = r.content.decode().lower()
    assert "error" not in raw
    assert "<html" not in raw
