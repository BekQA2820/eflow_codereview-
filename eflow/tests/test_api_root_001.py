import pytest
from unittest.mock import Mock
import json

MANIFEST = "/api/v1/manifest"


def test_hidden_widget_excluded_and_layout_recalculated(
    api_client, auth_header, mocker, mock_s3
):
    """
    Проверяем:
    - скрытый виджет (visible=False) не возвращается клиенту
    - layout корректно пересчитывается
    - JSON валиден
    - Content-Type = application/json
    - нет внутренних полей
    """

    # ---------------------------------------------------------
    # 1. Подготовка: два состояния widgets.yaml, до и после
    # ---------------------------------------------------------
    registry_before = {
        "widgets": [
            {"id": "w1", "visible": True,  "position": {"row": 0, "col": 0, "width": 2}},
            {"id": "w2", "visible": True,  "position": {"row": 0, "col": 2, "width": 2}},
        ]
    }

    registry_after = {
        "widgets": [
            {"id": "w1", "visible": True,  "position": {"row": 0, "col": 0, "width": 2}},
            {"id": "w2", "visible": False, "position": {"row": 0, "col": 2, "width": 2}},
        ]
    }

    # В S3 сначала лежит нормальная версия, потом — скрытая
    def fake_get_object(bucket, key):
        body = registry_after if fake_get_object.called else registry_before
        fake_get_object.called = True
        return {"Body": Mock(read=lambda: json.dumps(body).encode())}

    fake_get_object.called = False
    mock_s3.get_object.side_effect = fake_get_object

    # ---------------------------------------------------------
    # 2. Мокаем два ответа backend: до скрытия и после скрытия
    # ---------------------------------------------------------

    manifest_before = {
        "widgets": [
            {"id": "w1", "position": {"row": 0, "col": 0, "width": 2}},
            {"id": "w2", "position": {"row": 0, "col": 2, "width": 2}},
        ],
        "layout": {"rows": 1, "columns": 4},
    }

    manifest_after = {
        "widgets": [
            {"id": "w1", "position": {"row": 0, "col": 0, "width": 2}}
        ],
        "layout": {"rows": 1, "columns": 2},  # layout пересчитан!
    }

    r1 = Mock()
    r1.status_code = 200
    r1.headers = {"Content-Type": "application/json", "X-Cache": "MISS"}
    r1.json.return_value = manifest_before

    r2 = Mock()
    r2.status_code = 200
    r2.headers = {"Content-Type": "application/json", "X-Cache": "MISS"}
    r2.json.return_value = manifest_after

    mocker.patch("requests.get", side_effect=[r1, r2])

    # ---------------------------------------------------------
    # 3. Первый запрос — скрытый виджет ещё присутствует
    # ---------------------------------------------------------
    resp1 = api_client.get(MANIFEST, headers=auth_header)
    assert resp1.status_code == 200
    assert resp1.headers["Content-Type"].startswith("application/json")

    data1 = resp1.json()
    assert len(data1["widgets"]) == 2, "До скрытия должно быть 2 виджета"

    # ---------------------------------------------------------
    # 4. Второй запрос — виджет скрыт
    # ---------------------------------------------------------
    resp2 = api_client.get(MANIFEST, headers=auth_header)
    assert resp2.status_code == 200

    data2 = resp2.json()

    assert all(w["id"] != "w2" for w in data2["widgets"]), \
        "Скрытый виджет w2 не должен присутствовать в выдаче"

    # ---------------------------------------------------------
    # 5. Layout должен быть пересчитан
    # ---------------------------------------------------------
    assert data2["layout"]["columns"] == 2, \
        "Layout должен быть уплотнён после скрытия виджета"

    # Нет внутренних полей (безопасность)
    forbidden = {"internalFlags", "backendOnly", "serviceRouting"}
    def walk(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                yield k
                yield from walk(v)
        elif isinstance(obj, list):
            for x in obj:
                yield from walk(x)

    for key in walk(data2):
        assert key not in forbidden, f"Запрещённое поле найдено: {key}"
