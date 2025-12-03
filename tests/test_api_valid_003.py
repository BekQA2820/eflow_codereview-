
MANIFEST_PATH = "/api/v1/manifest"

DENY = {
    "internalFlags",
    "internalId",
    "serviceRouting",
    "debugInfo",
    "backendOnly",
    "requiredPermissions",
    "internalMeta",
    "configSource",
}


def test_api_valid_no_internal_fields(api_client, auth_header):
    r = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r.status_code == 200

    def walk(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                assert k not in DENY, f"Найдено запрещённое поле: {k}"
                walk(v)
        elif isinstance(obj, list):
            for i in obj:
                walk(i)

    walk(r.json())
