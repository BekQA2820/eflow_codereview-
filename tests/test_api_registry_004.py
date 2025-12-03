import pytest

MANIFEST_PATH = "/api/v1/manifest"


@pytest.mark.skip(reason="Требуется управляемый тестовый widgets.yaml в S3 и включенный fallback в backend")
def test_registry_fallback_on_corrupted_widgets_yaml(api_client, auth_header, s3_client):

    bucket = "widgets-config"
    key = "widgets.yaml"

    obj = s3_client.get_object(Bucket=bucket, Key=key)
    original_body = obj["Body"].read().decode("utf-8")

    corrupted = "widgets: [this is: : not valid: yaml: ]"

    try:
        s3_client.put_object(Bucket=bucket, Key=key, Body=corrupted.encode("utf-8"))

        r = api_client.get(MANIFEST_PATH, headers=auth_header)
        assert r.status_code == 200, "При битом widgets.yaml не должно быть 500"

        x_cache = r.headers.get("X-Cache", "").lower()
        # Ожидается, что backend использует fallback на предыдущий валидный registry
        if x_cache:
            assert "hit" in x_cache

    finally:
        s3_client.put_object(Bucket=bucket, Key=key, Body=original_body.encode("utf-8"))
