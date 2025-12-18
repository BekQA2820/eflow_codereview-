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
    """Универсальный мок объекта requests.get"""
    def __init__(self, status_code=200, headers=None, json_data=None):
        self.status_code = status_code
        self.headers = headers or {}
        self._json = json_data

    def json(self):
        return self._json


def has_forbidden_fields(obj, path="root"):
    """
    Рекурсивная проверка отсутствия запрещённых внутренних полей.
    Корректная версия (исправлено по замечанию сеньора).
    """
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in FORBIDDEN_FIELDS:
                return f"Запрещённое поле '{key}' обнаружено по пути '{path}'"
            deeper = has_forbidden_fields(value, f"{path}.{key}")
            if deeper:
                return deeper
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            deeper = has_forbidden_fields(value, f"{path}[{i}]")
            if deeper:
                return deeper
    return None


def test_layout_positions_and_no_overlap(api_client, auth_header, mocker):
    """
    API LAYOUT 002

    Проверяем корректность:
    - координат row/col/width/height
    - отсутствие пересечений
    - корректность границ layout
    - отсутствие внутренних полей (deny-list)
    """

    manifest_body = {
        "version": "1",
        "generatedAt": "2025-02-01T10:00:00Z",
        "layout": {"rows": 3, "columns": 4, "gridType": "fixed"},
        "widgets": [
            {
                "id": "w1",
                "type": "mfe",
                "position": {"row": 0, "col": 0, "width": 2, "height": 1},
            },
            {
                "id": "w2",
                "type": "link",
                "position": {"row": 0, "col": 2, "width": 2, "height": 1},
            },
            {
                "id": "w3",
                "type": "container",
                "position": {"row": 1, "col": 0, "width": 4, "height": 1},
            },
        ],
    }

    mocker.patch(
        "requests.get",
        return_value=DummyResponse(
            status_code=200,
            headers={"Content-Type": "application/json"},
            json_data=manifest_body,
        ),
    )

    resp = api_client.get(MANIFEST_PATH, headers=auth_header)

    # ---------------- HTTP ----------------
    assert resp.status_code == 200, f"Ожидаем 200, получили {resp.status_code}"
    ctype = resp.headers.get("Content-Type", "")
    assert ctype.startswith("application/json"), f"Неверный Content-Type: {ctype}"

    # ---------------- JSON ----------------
    body = resp.json()
    assert isinstance(body, dict), "Корневой объект JSON должен быть dict"

    # layout обязательный
    assert "layout" in body, "Поле layout обязательно"
    layout = body["layout"]
    assert isinstance(layout, dict), "layout должен быть объектом"

    assert "rows" in layout and isinstance(layout["rows"], int)
    assert "columns" in layout and isinstance(layout["columns"], int)
    assert layout["rows"] > 0
    assert layout["columns"] > 0

    # widgets обязательный
    assert "widgets" in body, "Поле widgets обязательно"
    widgets = body["widgets"]
    assert isinstance(widgets, list), "widgets должен быть списком"

    # ---------- Проверка пересечений ----------
    grid = [[None for _ in range(layout["columns"])] for _ in range(layout["rows"])]

    for i, widget in enumerate(widgets):
        assert isinstance(widget, dict), f"widget[{i}] должен быть dict"

        assert "position" in widget, f"widget[{i}] должен содержать position"
        pos = widget["position"]
        assert isinstance(pos, dict), f"position widget[{i}] должен быть dict"

        # обязательные координаты
        for field in ("row", "col", "width"):
            assert field in pos, f"position.{field} обязателен в widget[{i}]"
            assert isinstance(pos[field], int), f"position.{field} должен быть int"

        row = pos["row"]
        col = pos["col"]
        width = pos["width"]
        height = pos.get("height", 1)

        # проверка типов и границ
        assert isinstance(height, int), f"position.height должен быть int (widget[{i}])"
        assert height >= 1, f"height >= 1 (widget[{i}])"

        assert row >= 0 and row < layout["rows"], f"row выходит за границы layout (widget[{i}])"
        assert col >= 0 and col < layout["columns"], f"col выходит за границы layout (widget[{i}])"
        assert col + width <= layout["columns"], f"widget[{i}] выходит за правую границу"
        assert row + height <= layout["rows"], f"widget[{i}] выходит за нижнюю границу"

        # проверка пересечений ячеек
        for r in range(row, row + height):
            for c in range(col, col + width):
                assert grid[r][c] is None, \
                    f"Пересечение виджетов: widget[{i}] перекрывает widget '{grid[r][c]}'"
                grid[r][c] = widget["id"]

    # --------- Проверка deny-list ---------
    err = has_forbidden_fields(body)
    assert not err, f"Обнаружено запрещённое внутреннее поле: {err}"
