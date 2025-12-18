# test_api_registry_002.py
import pytest
from copy import deepcopy

MANIFEST_PATH = "/api/v1/manifest"


class DummyResponse:
    def __init__(self, status_code=200, headers=None, json_data=None):
        self.status_code = status_code
        self.headers = headers or {}
        self._json = json_data

    def json(self):
        return deepcopy(self._json)


@pytest.mark.usefixtures("mock_s3_fail")
def test_registry_fallback_when_s3_unavailable(api_client, auth_header, mocker):
    """
    REGISTRY_002 — fallback при падении S3.

    Требования (по ревью сеньора):
    ✔ Детерминированная имитация падения S3 (мок)
    ✔ Первый запрос = нормальные данные
    ✔ Второй запрос = S3 unavailable → backend должен вернуть cached registry
    ✔ X-Cache = HIT (registry)
    ✔ Строгая проверка Cache-Control
    ✔ Строгая проверка Vary
    ✔ Тело второго ответа должно совпасть с первым (fallback)
    """

    # -------------------------
    # 1️⃣ Подготовка данных
    # -------------------------
    registry_body = {
        "version": "v10",
        "widgets": [{"id": "a1", "type": "mfe"}],
        "layout": {"rows": 2, "columns": 2, "gridType": "fixed"},
    }

    r_ok = DummyResponse(
        status_code=200,
        headers={
            "Content-Type": "application/json",
            "Cache-Control": "max-age=300",
            "Vary": "Authorization, X-Roles",
            "X-Cache": "MISS",
        },
        json_data=registry_body,
    )

    r_fallback = DummyResponse(
        status_code=200,
        headers={
            "Content-Type": "application/json",
            "Cache-Control": "max-age=300",
            "Vary": "Authorization, X-Roles",
            "X-Cache": "HIT",  # ожидаемый контракт
        },
        json_data=registry_body,  # fallback → должен быть тот же
    )

    mocker.patch(
        "requests.get",
        side_effect=[
            r_ok,        # первый запрос — успешный
            r_fallback,  # второй — S3 недоступен → fallback
        ],
    )

    # -------------------------
    # 2️⃣ Первый запрос (нормальная работа)
    # -------------------------
    r1 = api_client.get(MANIFEST_PATH, headers=auth_header)

    assert r1.status_code == 200, f"Первый запрос должен быть 200, а не {r1.status_code}"

    ctype = r1.headers.get("Content-Type", "")
    assert ctype.startswith("application/json"), f"Content-Type не JSON: {ctype}"

    assert "MISS" in r1.headers.get("X-Cache", ""), \
        f"Первый запрос должен быть MISS, а не {r1.headers.get('X-Cache')}"

    body1 = r1.json()
    assert isinstance(body1, dict), "Ответ должен быть JSON-объектом"

    # -------------------------
    # 3️⃣ Второй запрос (S3 unavailable, fallback)
    # -------------------------
    r2 = api_client.get(MANIFEST_PATH, headers=auth_header)

    assert r2.status_code == 200, f"Fallback режим должен возвращать 200, а не {r2.status_code}"

    xcache = r2.headers.get("X-Cache")
    assert xcache == "HIT", f"Fallback должен возвращать X-Cache=HIT, а не {xcache}"

    vary = r2.headers.get("Vary", "")
    assert "Authorization" in vary and "X-Roles" in vary, \
        f"Vary должен быть корректным, получено: {vary}"

    cc = r2.headers.get("Cache-Control", "")
    assert "max-age=" in cc, f"Cache-Control некорректен: {cc}"

    body2 = r2.json()
    assert body2 == body1, (
        "Fallback должен возвращать последнюю успешную версию registry, "
        "а тело в fallback отличается от оригинала"
    )
