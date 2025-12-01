import json
from jsonschema import validate, ValidationError

DENY_FIELDS = {"requiredRoles", "internalFlags"}

def test_manifest_schema_full_validation(api_client, auth_header, manifest_schema):
    response = api_client.get("/api/v1/manifest", headers=auth_header)
    assert response.status_code == 200

    manifest = response.json()

    # JSON Schema validation
    validate(instance=manifest, schema=manifest_schema)

    widget_ids = set()
    for w in manifest["widgets"]:
        # Уникальные id
        assert w["id"] not in widget_ids, "Duplicate widget id found"
        widget_ids.add(w["id"])

        # allowed size ranges
        assert 1 <= w["size"]["width"] <= 12
        assert 1 <= w["size"]["height"] <= 12

        # position range
        assert w["position"]["x"] >= 0
        assert w["position"]["y"] >= 0

        # URL correctness
        assert w["mfe"].startswith("https://"), "Widget mfe must be HTTPS"

        # deny-list fields NOT allowed
        for f in DENY_FIELDS:
            assert f not in w, f"Field '{f}' must NOT be present"
