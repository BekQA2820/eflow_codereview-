
import pytest

MANIFEST_PATH = "/api/v1/manifest"


@pytest.mark.skip(reason="Требуется окружение, которое умеет эмулировать падение S3 для backend")
def test_registry_fallback_on_s3_error(api_client, auth_header):

    # Шаг 1: прогрев (кэшируем registry)
    r1 = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r1.status_code == 200

    # Шаг 2: тут должен быть триггер падения S3 для backend
    # TODO: интеграция с флагом/фичей, который переключает backend в режим "S3 недоступен"

    # Шаг 3: запрос в режиме падения S3 - ожидаем fallback на закэшированный registry
    r2 = api_client.get(MANIFEST_PATH, headers=auth_header)

    assert r2.status_code == 200
    x_cache = r2.headers.get("X-Cache", "").lower()
    # ожидаем, что backend использует кэш registry
    assert "hit" in x_cache

    # Проверка заголовков кеширования
    cache_control = r2.headers.get("Cache-Control", "")
    assert cache_control  # какой-то политики кэша быть должно

    vary = r2.headers.get("Vary", "").lower()
    assert "authorization" in vary or "x-roles" in vary
