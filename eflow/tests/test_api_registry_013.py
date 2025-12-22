import json

MANIFEST_PATH = "/api/v1/manifest"


def test_registry_recovers_after_s3_restore(mocker, api_client):
    fallback_manifest = {
        "widgets": [
            {"id": "old", "type": "mfe", "visible": True, "position": {"row": 0, "col": 0, "width": 1}}
        ],
        "layout": {"rows": 1, "columns": 1, "gridType": "fixed"},
        "version": "1",
    }

    new_manifest = {
        "widgets": [
            {"id": "new", "type": "mfe", "visible": True, "position": {"row": 0, "col": 0, "width": 2}}
        ],
        "layout": {"rows": 1, "columns": 2, "gridType": "fixed"},
        "version": "2",
    }

    r_fallback = mocker.Mock()
    r_fallback.status_code = 200
    r_fallback.headers = {
        "Content-Type": "application/json",
        "X-Cache": "HIT (registry fallback)",
    }
    r_fallback.json.return_value = fallback_manifest
    r_fallback.content = json.dumps(fallback_manifest).encode()

    r_rebuild = mocker.Mock()
    r_rebuild.status_code = 200
    r_rebuild.headers = {
        "Content-Type": "application/json",
        "X-Cache": "MISS",
    }
    r_rebuild.json.return_value = new_manifest
    r_rebuild.content = json.dumps(new_manifest).encode()

    mocker.patch("requests.get", side_effect=[r_fallback, r_rebuild])

    r1 = api_client.get(MANIFEST_PATH)
    r2 = api_client.get(MANIFEST_PATH)

    assert r1.json() == fallback_manifest
    assert "fallback" in r1.headers.get("X-Cache", "").lower()

    assert r2.json() == new_manifest
    assert r2.headers.get("X-Cache") == "MISS"
    assert r1.json() != r2.json()
