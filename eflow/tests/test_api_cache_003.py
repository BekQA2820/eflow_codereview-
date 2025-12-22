

import pytest


class DummyResponse:
    def __init__(self, status_code=200, headers=None, json_data=None, content=b""):
        self.status_code = status_code
        self.headers = headers or {}
        self._json = json_data
        self.content = content

    def json(self):
        return self._json


MANIFEST_PATH = "/api/v1/manifest"


def test_manifest_cache_miss_then_hit(api_client, auth_header, mocker):
    # Готовим два детерминированных ответа backend
    body = {"version": "1", "widgets": [], "layout": {"rows": 1, "columns": 1}}

    r_miss = DummyResponse(
        status_code=200,
        headers={
            "Content-Type": "application/json",
            "X-Cache": "MISS",
            "Cache-Control": "max-age=300",
        },
        json_data=body,
    )
    r_hit = DummyResponse(
        status_code=200,
        headers={
            "Content-Type": "application/json",
            "X-Cache": "HIT",
            "Cache-Control": "max-age=300",
        },
        json_data=body,
    )

    mock_get = mocker.patch(
        "requests.get",
        side_effect=[r_miss, r_hit],
    )

    # R1 — ожидаем MISS
    r1 = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r1.status_code == 200, f"Первый запрос должен вернуть 200, а не {r1.status_code}"
    assert r1.headers.get("Content-Type", "").startswith(
        "application/json"
    ), f"Ожидается JSON, а не {r1.headers.get('Content-Type')}"
    assert "X-Cache" in r1.headers, "Для R1 обязателен заголовок X-Cache"
    assert r1.headers["X-Cache"] == "MISS", f"R1 должен быть MISS, а не {r1.headers['X-Cache']}"

    # R2 — ожидаем HIT, тот же контент
    r2 = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r2.status_code == 200, f"Второй запрос должен вернуть 200, а не {r2.status_code}"
    assert "X-Cache" in r2.headers, "Для R2 обязателен заголовок X-Cache"
    assert r2.headers["X-Cache"] == "HIT", f"R2 должен быть HIT, а не {r2.headers['X-Cache']}"
    assert r2.headers.get("Content-Type") == r1.headers.get(
        "Content-Type"
    ), "Тип контента должен совпадать для MISS и HIT"
    assert r2.json() == r1.json(), "Содержимое manifest при HIT должно совпадать с MISS"

    assert mock_get.call_count == 2, "Ожидаем ровно два HTTP-вызова backend"
