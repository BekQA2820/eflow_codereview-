
import pytest

MANIFEST_PATH = "/api/v1/manifest"

@pytest.mark.skip(reason="Требуется окружение с управляемым S3 и обновлением widgets.yaml")
def test_registry_recovery_after_s3_back_online(api_client, auth_header):

    # TODO: включить режим "S3 недоступен" для backend
    r_fallback = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r_fallback.status_code == 200
    fallback_body = r_fallback.json()

    # Этап 2: восстановление S3 и изменение widgets.yaml
    # TODO: убрать режим "S3 недоступен" и обновить widgets.yaml в S3

    # Этап 3: повторный запрос должен вернуть новую версию
    r_new = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r_new.status_code == 200
    new_body = r_new.json()

    assert new_body != fallback_body, "После восстановления S3 должен вернуться обновлённый registry"
