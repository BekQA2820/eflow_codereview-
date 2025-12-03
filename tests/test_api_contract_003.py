import re

MANIFEST_PATH = "/api/v1/manifest"


def test_api_contract_generated_at_iso8601(api_client, auth_header):
    r = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r.status_code == 200

    ts = r.json()["generatedAt"]

    pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z$"
    assert re.match(pattern, ts), f"Некорректный формат generatedAt: {ts}"
