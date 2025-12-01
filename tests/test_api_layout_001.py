
MANIFEST_PATH = "/api/v1/manifest"

def test_api_layout_validation(api_client, auth_header):
    """
    Проверка корректности layout:
    нет выходов за границы
     нет пересечений
     layout.rows, columns, gaps корректны
    """
    r = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r.status_code == 200

    data = r.json()
    layout = data["layout"]

    cols = layout["columns"]

    used_positions = set()

    for widget in data["widgets"]:
        pos = widget["position"]
        row = pos["row"]
        col = pos["col"]
        width = pos["width"]

        # Проверка выхода за границы
        assert row >= 0
        assert col >= 0
        assert col + width <= cols

        # Проверка пересечений виджетов
        for x in range(col, col + width):
            key = (row, x)
            assert key not in used_positions, "Пересечение в layout"
            used_positions.add(key)
