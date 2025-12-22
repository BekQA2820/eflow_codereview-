import json

MANIFEST_PATH = "/api/v1/manifest"


def test_registry_unavailable_uses_cached_version(mocker, api_client):
    cached_manifest = {
        "widgets": [
            {"id": "cached", "type": "mfe", "visible": True, "position": {"row": 0, "col": 0, "width": 2}}
        ],
        "layout": {"rows": 1, "columns": 2, "gridType": "fixed"},
        "version": "100",
    }

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {
        "Content-Type": "application/json",
        "X-Cache": "HIT (registry fallback)",
        "Vary": "Authorization, X-Roles",
    }
    resp.json.return_value = cached_manifest
    resp.content = json.dumps(cached_manifest).encode()

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(MANIFEST_PATH)

    assert r.status_code == 200
    assert r.json() == cached_manifest
    assert "fallback" in r.headers.get("X-Cache", "").lower()

    raw = r.content.decode().lower()
    assert "errorresponse" not in raw
    assert "<html" not in raw
    assert "stacktrace" not in raw
