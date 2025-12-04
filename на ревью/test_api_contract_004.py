import pytest

MANIFEST_PATH = "/api/v1/manifest"


@pytest.mark.skip(reason="Требуется управляемая модификация widgets.yaml в S3")
def test_api_contract_version_changes(api_client, auth_header):
    r1 = api_client.get(MANIFEST_PATH, headers=auth_header)
    v1 = r1.json().get("version")

    # TODO изменить widgets.yaml

    r2 = api_client.get(MANIFEST_PATH, headers=auth_header)
    v2 = r2.json().get("version")

    assert v1 != v2
