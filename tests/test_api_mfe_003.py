import pytest

MANIFEST_PATH = "/api/v1/manifest"


@pytest.mark.skip(reason="Требуется управляемое изменение widgets.yaml в S3")
def test_api_mfe_hidden_widget_filtered(api_client, auth_header, s3_client):

    # TODO: выбрать тестовый widget.id и обновить widgets.yaml
    assert True
