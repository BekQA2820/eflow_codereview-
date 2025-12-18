import json

MANIFEST_PATH = "/api/v1/manifest"


def test_registry_yaml_syntax_error_uses_previous_version(mocker, api_client):
    previous_manifest = {
        "widgets": [
            {"id": "safe", "type": "mfe", "visible": True, "position": {"row": 0, "col": 0, "width": 1}}
        ],
        "layout": {"rows": 1, "columns": 1, "gridType": "fixed"},
        "version": "42",
    }

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {
        "Content-Type": "application/json",
        "X-Cache": "HIT (registry fallback)",
    }
    resp.json.return_value = previous_manifest
    resp.content = json.dumps(previous_manifest).encode()

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(MANIFEST_PATH)

    assert r.status_code == 200
    assert r.json() == previous_manifest
    assert "fallback" in r.headers.get("X-Cache", "").lower()

    raw = r.content.decode().lower()
    assert "exception" not in raw
    assert "stacktrace" not in raw
    assert "<html" not in raw
