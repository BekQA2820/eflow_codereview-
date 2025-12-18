import json

MANIFEST_PATH = "/api/v1/manifest"


def test_registry_missing_widgets_field_fallback(mocker, api_client):
    fallback_manifest = {
        "widgets": [
            {"id": "baseline", "type": "mfe", "visible": True, "position": {"row": 0, "col": 0, "width": 1}}
        ],
        "layout": {"rows": 1, "columns": 1, "gridType": "fixed"},
        "version": "7",
    }

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {
        "Content-Type": "application/json",
        "X-Cache": "HIT (registry fallback)",
    }
    resp.json.return_value = fallback_manifest
    resp.content = json.dumps(fallback_manifest).encode()

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(MANIFEST_PATH)

    assert r.status_code == 200
    assert r.json() == fallback_manifest
    assert "widgets" in r.json()
    assert isinstance(r.json()["widgets"], list)

    raw = r.content.decode().lower()
    assert "errorresponse" not in raw
    assert "<html" not in raw
