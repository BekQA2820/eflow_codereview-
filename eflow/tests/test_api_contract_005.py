import pytest

MANIFEST_PATH = "/api/v1/manifest"

# Допустимые типы (согласно текущей спецификации)
ALLOWED_TYPES = {"mfe", "link", "container", "empty"}


def test_widget_type_values_and_related_fields(api_client, auth_header):
    """
    API CONTRACT 005

    Проверяем:
    - наличие поля widgets и его тип
    - что каждый widget содержит type
    - что type ∈ ALLOWED_TYPES
    - базовые per-type инварианты (минимально по спецификации)
    """

    r = api_client.get(MANIFEST_PATH, headers=auth_header)

    assert r.status_code == 200, f"Ожидаем 200 OK, получили {r.status_code}"
    ctype = r.headers.get("Content-Type", "")
    assert ctype.startswith("application/json"), (
        f"Ожидаем JSON-ответ, Content-Type={ctype!r}"
    )

    try:
        data = r.json()
    except Exception as e:
        pytest.fail(f"Ответ не является валидным JSON: {e}")

    assert isinstance(data, dict), "Корневой объект manifest должен быть JSON-объектом"

    assert "widgets" in data, "В manifest отсутствует обязательное поле 'widgets'"
    widgets = data["widgets"]
    assert isinstance(widgets, list), "'widgets' должен быть массивом"

    assert widgets, "Список widgets не должен быть пустым"

    for idx, widget in enumerate(widgets):
        assert isinstance(widget, dict), f"widget[{idx}] должен быть объектом JSON"

        assert "type" in widget, f"В widget[{idx}] отсутствует поле 'type'"
        wtype = widget["type"]
        assert isinstance(wtype, str), f"widget[{idx}].type должен быть строкой"
        assert wtype.strip(), f"widget[{idx}].type не должен быть пустым"

        assert wtype in ALLOWED_TYPES, (
            f"widget[{idx}].type={wtype!r} не входит в список разрешённых типов {sorted(ALLOWED_TYPES)}. "
            "Либо backend вернул неизвестный тип, либо нужно обновить тест/спеку."
        )

        # Дополнительные per-type проверки, мягкие — только то, что уже описано в доке:
        if wtype == "mfe":
            # Для MFE ожидаем, что есть поле 'mfe' (URL remoteEntry) или аналогичный endpoint
            assert "mfe" in widget, f"widget[{idx}] с type='mfe' должен содержать поле 'mfe'"
            assert isinstance(widget["mfe"], str), f"widget[{idx}].mfe должен быть строкой (URL)"

        if wtype == "link":
            # Для ссылочного виджета ожидаем url/href
            url = widget.get("url") or widget.get("href")
            assert isinstance(url, str) and url.strip(), (
                f"widget[{idx}] с type='link' должен иметь непустой url/href"
            )

        if wtype == "container":
            # Для контейнеров допустимо наличие children (если это предусмотрено).
            # Не ломаемся, если children нет, но если есть — проверяем тип.
            if "children" in widget:
                assert isinstance(widget["children"], list), (
                    f"widget[{idx}] с type='container' поле 'children' должно быть массивом"
                )

        # Для type="empty" спец-проверок не вводим: сам факт типа уже важен.
