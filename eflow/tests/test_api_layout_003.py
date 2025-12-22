import pytest

MANIFEST_PATH = "/api/v1/manifest"

FORBIDDEN_FIELDS = {
    "internalFlags",
    "internalId",
    "debugInfo",
    "backendOnly",
    "serviceRouting",
}


class DummyResponse:
    """Мок объекта requests.get"""
    def __init__(self, status_code=200, headers=None, json_data=None):
        self.status_code = status_code
        self.headers = headers or {}
        self._json = json_data

    def json(self):
        return self._json


def has_forbidden_fields(obj, path="root"):
    """Рекурсивная проверка внутренних полей (исправленный вариант)"""
    if isinstance(obj, dict):
        for key, val in obj.items():
            if key in FORBIDDEN_FIELDS:
                return f"Запрещённое поле '{key}' обнаружено в {path}"
            deeper = has_forbidden_fields(val, f"{path}.{key}")
            if deeper:
                return deeper
    elif isinstance(obj, list):
        for i, val in enumerate(obj):
            deeper = has_forbidden_fields(val, f"{path}[{i}]")
            if deeper:
                return deeper
    return None


def test_layout_sorting_and_determinism(api_client, auth_header, mocker):


    widgets_sorted = [
        {"id": "a-widget", "type": "mfe", "position": {"row": 0, "col": 0, "width": 2}},
        {"id": "b-widget", "type": "link", "position": {"row": 0, "col": 2, "width": 1}},
        {"id": "c-widget", "type": "container", "position": {"row": 1, "col": 0, "width": 3}},
    ]

    manifest_body = {
        "version": "1",
        "generatedAt": "2025-02-01T10:00:00Z",
        "layout": {"rows": 2, "columns": 3, "gridType": "fixed"},
        "widgets": widgets_sorted,
    }

    # две идентичные выдачи → проверяем детерминизм
    mocker.patch(
        "requests.get",
        side_effect=[
            DummyResponse(200, {"Content-Type": "application/json"}, manifest_body),
            DummyResponse(200, {"Content-Type": "application/json"}, manifest_body),
        ],
    )

    # ---------------- R1 -----------------
    r1 = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r1.status_code == 200
    assert r1.headers.get("Content-Type", "").startswith("application/json")
    b1 = r1.json()
    assert isinstance(b1, dict)
    assert "widgets" in b1 and isinstance(b1["widgets"], list)

    # ---------------- R2 ----------------
    r2 = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r2.status_code == 200
    assert r2.headers.get("Content-Type", "").startswith("application/json")
    b2 = r2.json()
    assert isinstance(b2, dict)
    assert "widgets" in b2 and isinstance(b2["widgets"], list)

    w1 = b1["widgets"]
    w2 = b2["widgets"]

    # ----------- Проверка детерминизма -----------
    assert w1 == w2, (
        "Порядок widgets должен быть детерминированным.\n"
        f"R1: {w1}\nR2: {w2}"
    )

    # ----------- Проверка корректной сортировки -----------
    ids = [w["id"] for w in w1]
    expected_sorted = sorted(ids)

    assert ids == expected_sorted, (
        "Widgets должны быть отсортированы по id (или контрактному правилу).\n"
        f"Получено: {ids}\nОжидалось: {expected_sorted}"
    )

    # ----------- Проверка обязательных полей и типов -----------
    for i, w in enumerate(w1):
        assert isinstance(w, dict), f"widget[{i}] должен быть dict"

        assert "id" in w and isinstance(w["id"], str), f"widget[{i}].id обязателен"
        assert "type" in w, f"widget[{i}].type обязателен"
        assert "position" in w and isinstance(w["position"], dict), f"widget[{i}].position обязателен"

        pos = w["position"]
        for field in ("row", "col", "width"):
            assert field in pos, f"widget[{i}].position.{field} обязателен"
            assert isinstance(pos[field], int), f"{field} должен быть int"

    # ----------- Проверка отсутствия внутренних полей (deny-list) -----------
    err = has_forbidden_fields(b1)
    assert not err, f"Обнаружено запрещённое внутреннее поле: {err}"
