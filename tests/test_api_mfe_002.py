import pytest
import requests

MANIFEST_PATH = "/api/v1/manifest"

FORBIDDEN_FIELDS = {
    "internalFlags",
    "internalId",
    "debugInfo",
    "backendOnly",
    "serviceRouting",
}


class DummyResponse:
    """Мок ответа для requests.get/requests.head"""
    def __init__(self, status_code=200, headers=None, json_data=None):
        self.status_code = status_code
        self.headers = headers or {}
        self._json = json_data

    def json(self):
        return self._json


def has_forbidden(obj, path="root"):
    """Рекурсивная проверка на deny-list"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in FORBIDDEN_FIELDS:
                return f"{path}: найдено запрещённое поле '{k}'"
            deeper = has_forbidden(v, f"{path}.{k}")
            if deeper:
                return deeper
    if isinstance(obj, list):
        for i, v in enumerate(obj):
            deeper = has_forbidden(v, f"{path}[{i}]")
            if deeper:
                return deeper
    return None


def test_mfe_remote_entry_accessibility(api_client, auth_header, mocker):

    manifest_body = {
        "version": "1",
        "generatedAt": "2025-02-01T00:00:00Z",
        "layout": {"rows": 2, "columns": 3, "gridType": "fixed"},
        "widgets": [
            {
                "id": "profile-mfe",
                "type": "mfe",
                "mfe": {"url": "https://cdn.example.com/profile/remoteEntry.js"},
                "position": {"row": 0, "col": 0, "width": 2},
            },
            {
                "id": "dashboard-mfe",
                "type": "mfe",
                "mfe": {"url": "https://cdn.example.com/dashboard/remoteEntry.js"},
                "position": {"row": 1, "col": 0, "width": 3},
            },
        ],
    }

    # ---------- Мокаем manifest ----------
    mocker.patch(
        "requests.get",
        return_value=DummyResponse(
            200,
            {"Content-Type": "application/json"},
            manifest_body,
        ),
    )

    # ---------- Мокаем HEAD / GET запросы для MFE ----------
    def mock_head(url, *args, **kwargs):
        # корректная имитация CDN → HEAD OK
        return DummyResponse(200, {"Content-Type": "application/javascript"})

    mocker.patch("requests.head", side_effect=mock_head)

    # ---------- R1: получаем manifest ----------
    r = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r.status_code == 200
    assert r.headers.get("Content-Type", "").startswith("application/json")

    body = r.json()
    assert isinstance(body, dict), "Manifest должен быть JSON объектом"

    # обязательные поля
    assert "widgets" in body, "Поле widgets обязательно"
    assert isinstance(body["widgets"], list), "widgets должен быть списком"

    # проверка отсутствия внутренних полей
    err = has_forbidden(body)
    assert not err, f"Обнаружено запрещённое внутреннее поле: {err}"

    # ---------- Проверяем MFE ----------
    for i, w in enumerate(body["widgets"]):
        assert isinstance(w, dict), f"widget[{i}] должен быть dict"

        # обязательные поля
        assert "id" in w, f"widget[{i}] отсутствует id"
        assert "type" in w, f"widget[{i}] отсутствует type"
        assert w["type"] == "mfe", f"widget[{i}] должен быть type='mfe'"

        assert "mfe" in w and isinstance(w["mfe"], dict), f"widget[{i}].mfe обязателен"

        url = w["mfe"].get("url")
        assert isinstance(url, str) and url.startswith("http"), (
            f"widget[{i}].mfe.url должен быть валидным URL, получено: {url}"
        )

        # ---------- HEAD запрос для проверки доступности ----------
        resp = requests.head(url)

        assert resp.status_code in (200, 301, 302), (
            f"HEAD {url} должен возвращать 200 или редирект, "
            f"получено: {resp.status_code}"
        )

        ctype = resp.headers.get("Content-Type", "")
        assert (
            "javascript" in ctype.lower()
            or "application/octet-stream" in ctype.lower()
            or "text/plain" in ctype.lower()
        ), (
            f"Некорректный Content-Type для remoteEntry.js: {ctype}"
        )
