import json

MANIFEST_PATH = "/api/v1/manifest"

DENY_FIELDS = {
    "internalFlags",
    "internalId",
    "debugInfo",
    "backendOnly",
    "serviceRouting",
    "requiredPermissions",
    "internalMeta",
    "configSource",
}


def _walk_and_check(node, path="root"):
    if isinstance(node, dict):
        for k, v in node.items():
            assert k not in DENY_FIELDS, (
                f"Запрещённое поле '{k}' обнаружено по пути {path}"
            )
            _walk_and_check(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, item in enumerate(node):
            _walk_and_check(item, f"{path}[{i}]")


def test_manifest_has_no_deny_fields_on_any_level(mocker, api_client):
    """
    API SEC 011
    Глубокая проверка deny-list на всех уровнях JSON
    """

    manifest = {
        "layout": {"rows": 1, "columns": 3, "gridType": "fixed"},
        "widgets": [
            {
                "id": "widget-public",
                "type": "mfe",
                "visible": True,
                "position": {"row": 0, "col": 0, "width": 1},
                "mfe": "https://cdn.example.com/app/v1",
            }
        ],
        "version": "1.0",
    }

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {
        "Content-Type": "application/json",
        "X-Request-ID": "req-sec-011",
    }
    resp.json.return_value = manifest
    resp.text = json.dumps(manifest)

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(MANIFEST_PATH)

    assert r.status_code == 200
    data = r.json()

    _walk_and_check(data)
