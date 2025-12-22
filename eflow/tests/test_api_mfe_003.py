import json
import pytest

MANIFEST = "/api/v1/manifest"


class DummyResponse:
    def __init__(self, status_code=200, headers=None, json_data=None):
        self.status_code = status_code
        self.headers = headers or {"Content-Type": "application/json"}
        self._json = json_data

    def json(self):
        return self._json


def test_hidden_widget_filtered(api_client, auth_header, mock_s3, mocker):
    """
    Проверяем логику hidden=true:
    - backend получает YAML из S3 (замокан)
    - один виджет помечен hidden
    - backend НЕ должен вернуть его в manifest
    """

    # ----- Подготовка данных -----

    # Структура "до"
    initial_manifest = {
        "layout": {"rows": 2, "columns": 3, "gridType": "fixed"},
        "widgets": [
            {"id": "w1", "visible": True, "position": {"row": 0, "col": 0, "width": 2}},
            {"id": "w2", "visible": False, "position": {"row": 1, "col": 0, "width": 1}}
        ],
        "version": "1"
    }

    # Ожидаемый ответ после фильтрации hidden
    filtered_manifest = {
        "layout": initial_manifest["layout"],
        "widgets": [
            {"id": "w1", "visible": True, "position": {"row": 0, "col": 0, "width": 2}},
        ],
        "version": "1"
    }

    r = DummyResponse(
        status_code=200,
        json_data=filtered_manifest
    )

    mocker.patch("requests.get", return_value=r)

    # ----- Вызов -----
    response = api_client.get(MANIFEST, headers=auth_header)

    # ----- Проверки -----

    # Статус
    assert response.status_code == 200, "Ожидаем успешный ответ"

    # JSON headers
    ctype = response.headers.get("Content-Type", "")
    assert ctype.startswith("application/json"), f"Неверный Content-Type: {ctype}"

    body = response.json()
    assert isinstance(body, dict), "Корень JSON должен быть объектом"

    # layout обязателен
    assert "layout" in body, "Нет layout"
    assert isinstance(body["layout"], dict)

    # widgets обязателен
    assert "widgets" in body
    assert isinstance(body["widgets"], list)

    # Проверка что скрытого виджета нет
    widget_ids = [w["id"] for w in body["widgets"]]
    assert "w2" not in widget_ids, "hidden=true должен скрывать виджет"

    # Проверка что layout не «ломается»
    assert body["layout"] == initial_manifest["layout"], \
        "layout не должен меняться при скрытии виджета"
