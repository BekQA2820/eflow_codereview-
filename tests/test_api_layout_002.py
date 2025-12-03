MANIFEST_PATH = "/api/v1/manifest"


def test_layout_coordinates_and_no_overlaps(api_client, auth_header):
    r1 = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r1.status_code == 200
    manifest1 = r1.json()

    layout = manifest1.get("layout") or {}
    widgets = manifest1.get("widgets") or []

    columns = layout.get("columns")
    assert isinstance(columns, int) and columns >= 1

    # Проверка координат и размеров
    occupied_cells = set()

    for w in widgets:
        pos = w.get("position") or {}
        size = w.get("size") or {}

        row = pos.get("row")
        col = pos.get("col")
        width = size.get("width")

        assert isinstance(row, int) and row >= 0
        assert isinstance(col, int) and col >= 0
        assert isinstance(width, int) and width >= 1
        assert col + width <= columns

        # Проверка пересечений (по строкам + колонкам)
        height = size.get("height", 1)
        for dy in range(height):
            for dx in range(width):
                cell = (row + dy, col + dx)
                assert cell not in occupied_cells, f"Пересечение виджетов в ячейке {cell}"
                occupied_cells.add(cell)

    # Повторный запрос — layout должен быть детерминированным
    r2 = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r2.status_code == 200
    manifest2 = r2.json()

    assert manifest1.get("layout") == manifest2.get("layout")
    assert manifest1.get("widgets") == manifest2.get("widgets")

    # Проверка deny-list на layout уровне
    deny_fields = {"internalFlags", "internalId", "debugInfo", "backendOnly", "serviceRouting"}

    def has_forbidden_fields(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in deny_fields:
                    return True
                if has_forbidden_fields(v):
                    return True
        elif isinstance(obj, list):
            return any(has_forbidden_fields(i) for i in obj)
        return False

    assert not has_forbidden_fields(manifest1), "В манифесте найдены запрещённые внутренние поля"
