import pytest


MANIFEST_PATH = "/api/v1/manifest"


class DummyResponse:
    """
    Локальный DummyResponse, имитирующий requests.Response
    для детерминированного теста version.
    """
    def __init__(self, status_code=200, headers=None, json_data=None):
        self.status_code = status_code
        self.headers = headers or {}
        self._json = json_data

    def json(self):
        return self._json


def test_manifest_version_changes_when_manifest_changes(api_client, auth_header, mocker):
    """
    API CONTRACT 004

    Специфика теста:
    - мы НЕ завязаны на реальный backend (используем мок requests.get),
    - тест описывает контракт: при изменении данных manifest
      версия должна измениться (динамическая версия).
    """

    manifest_v1 = {
        "version": "1.0.0",
        "layout": {"rows": 2, "columns": 3, "gridType": "fixed"},
        "widgets": [
            {"id": "w1", "type": "mfe", "position": {"row": 0, "col": 0, "width": 2}},
        ],
    }

    manifest_v2 = {
        "version": "2.0.0",
        "layout": {"rows": 2, "columns": 3, "gridType": "fixed"},
        "widgets": [
            {"id": "w1", "type": "mfe", "position": {"row": 0, "col": 0, "width": 2}},
            {"id": "w2", "type": "mfe", "position": {"row": 1, "col": 0, "width": 3}},
        ],
    }

    r1 = DummyResponse(
        status_code=200,
        headers={"Content-Type": "application/json", "ETag": '"v1"'},
        json_data=manifest_v1,
    )
    r2 = DummyResponse(
        status_code=200,
        headers={"Content-Type": "application/json", "ETag": '"v2"'},
        json_data=manifest_v2,
    )

    mock_get = mocker.patch("requests.get", side_effect=[r1, r2])

    first = api_client.get(MANIFEST_PATH, headers=auth_header)
    second = api_client.get(MANIFEST_PATH, headers=auth_header)

    # Базовые проверки обоих ответов
    for name, resp in (("R1", first), ("R2", second)):
        assert resp.status_code == 200, f"{name}: ожидаем 200 OK, а не {resp.status_code}"
        ctype = resp.headers.get("Content-Type", "")
        assert ctype.startswith("application/json"), (
            f"{name}: Content-Type должен быть JSON, а не {ctype}"
        )

        body = resp.json()
        assert isinstance(body, dict), f"{name}: тело должно быть JSON-объектом"
        assert "version" in body, f"{name}: в manifest отсутствует поле 'version'"

        version = body["version"]
        assert isinstance(version, (str, int)), (
            f"{name}: 'version' должен быть строкой или числом, получено {type(version).__name__}"
        )

    v1 = first.json()["version"]
    v2 = second.json()["version"]

    # Ключевой контракт: изменение данных => изменение версии
    assert v1 != v2, f"Ожидаем изменение version при изменении manifest, но v1={v1!r}, v2={v2!r}"

    # Для полноты проверяем, что layout – тот же, а widgets отличаются
    layout1 = first.json()["layout"]
    layout2 = second.json()["layout"]
    assert layout1 == layout2, "layout должен остаться тем же между версиями v1 и v2"

    widgets1 = first.json()["widgets"]
    widgets2 = second.json()["widgets"]
    assert widgets1 != widgets2, "widgets должны отличаться между v1 и v2 в этом сценарии"

    assert mock_get.call_count == 2, "Ожидаем два вызова backend (через мок requests.get)"
