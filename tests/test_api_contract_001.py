import json
from jsonschema import validate


MANIFEST = "/api/v1/manifest"


def test_manifest_schema_validation(api_client, auth_header):
    r = api_client.get(MANIFEST, headers=auth_header)
    assert r.status_code == 200

    data = r.json()

    # Загружаем schema.json
    with open("schemas/manifest_schema.json", "r", encoding="utf-8") as f:
        schema = json.load(f)

    validate(instance=data, schema=schema)
