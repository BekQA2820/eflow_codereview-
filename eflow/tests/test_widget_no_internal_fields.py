MANIFEST = "/api/v1/manifest"


def test_widget_no_internal_fields(api_client, auth_header):
    r = api_client.get(MANIFEST, headers=auth_header)
    widgets = r.json().get("widgets", [])

    forbidden_fields = {"requiredRoles", "internalFlags"}

    for w in widgets:
        assert not any(f in w for f in forbidden_fields)
