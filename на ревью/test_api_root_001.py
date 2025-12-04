
import copy
import pytest

MANIFEST_PATH = "/api/v1/manifest"


@pytest.mark.skip(reason="Требуется доступ к реальному widgets.yaml в S3 и знание ID тестового виджета")
def test_hidden_visible_behavior(api_client, auth_header, s3_client):

    # TODO: подтянуть S3_BUCKET и ключ из переменных окружения либо фикстуры
    bucket = "widgets-config"
    key = "widgets.yaml"

    obj = s3_client.get_object(Bucket=bucket, Key=key)
    original_body = obj["Body"].read().decode("utf-8")

    # Резервная копия
    original_yaml = original_body

    try:
        # Здесь нужен реальный парсинг YAML - для примера можно использовать json-like структуру
        import yaml  # если добавите в requirements

        data = yaml.safe_load(original_body)

        # TODO: выбрать тестовый виджет по известному ID, например "delegations-widget"
        widgets = data.get("widgets", [])
        assert widgets, "widgets.yaml не содержит виджетов для теста"

        target = widgets[0]
        target_id = target["id"]

        # Меняем visible - false
        modified = copy.deepcopy(data)
        for w in modified["widgets"]:
            if w["id"] == target_id:
                w["visible"] = False

        new_body = yaml.safe_dump(modified, allow_unicode=True)

        # Заливаем назад в S3
        s3_client.put_object(Bucket=bucket, Key=key, Body=new_body.encode("utf-8"))

        # Запрашиваем манифест
        r = api_client.get(MANIFEST_PATH, headers=auth_header)
        assert r.status_code == 200
        manifest = r.json()

        ids = [w["id"] for w in manifest.get("widgets", [])]
        assert target_id not in ids, "Скрытый виджет не должен присутствовать в манифесте"

        # Проверка отсутствия дыр и пересечений - можно переиспользовать логику из LAYOUT 002
        # (опущено для краткости, но идея та же: пройти по grid и проверить заполнение)
    finally:
        # Восстанавливаем оригинальный widgets.yaml
        s3_client.put_object(Bucket=bucket, Key=key, Body=original_yaml.encode("utf-8"))
