MANIFEST = "/api/v1/manifest"


def test_layout_integrity(api_client, auth_header):
    r = api_client.get(MANIFEST, headers=auth_header)

    manifest = r.json()
    layout = manifest.get("layout")
    widgets = manifest.get("widgets", [])

    rows = layout.get("rows")
    cols = layout.get("columns")

    for w in widgets:
        pos = w.get("position", {})
        row = pos.get("row")
        col = pos.get("col")
        width = pos.get("width", 1)

        assert 0 <= row < rows
        assert 0 <= col < cols
        assert col + width <= cols

    # Проверка пересечений
    grid = set()
    for w in widgets:
        pos = w["position"]
        for x in range(pos["col"], pos["col"] + pos["width"]):
            cell = (pos["row"], x)
            assert cell not in grid, f"Пересечение в {cell}"
            grid.add(cell)
