MANIFEST_PATH = "/api/v1/manifest"


def test_api_contract_manifest_structure(api_client, auth_header):
    r = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r.status_code == 200

    data = r.json()

    assert isinstance(data.get("widgets"), list)
    assert isinstance(data.get("layout"), dict)
    assert isinstance(data["layout"].get("gridType"), str)
    assert isinstance(data.get("generatedAt"), str)

    deny = {"internalFlags", "internalId", "serviceRouting", "debugInfo", "backendOnly"}

    def walk(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                assert k not in deny
                walk(v)
        elif isinstance(obj, list):
            for i in obj:
                walk(i)

    walk(data)
