MANIFEST_PATH = "/api/v1/manifest"


def test_widgets_sorting_is_stable(api_client, auth_header):
    """
    Минимальная проверка:
    - порядок виджетов стабилен между запросами
    - нет рандомизации
    TODO: после уточнения алгоритма сортировки добавить строгую проверку по полю (например, id).
    """
    r1 = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r1.status_code == 200
    widgets1 = r1.json().get("widgets", [])

    r2 = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r2.status_code == 200
    widgets2 = r2.json().get("widgets", [])

    # Проверяем, что порядок стабилен
    assert widgets1 == widgets2, "Порядок виджетов должен быть детерминированным"
