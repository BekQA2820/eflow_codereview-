import pytest
import re

MANIFEST_PATH = "/api/v1/manifest"

# Допустимые паттерны:
# - kebab-case: some-widget-1
# - snake_case: some_widget_1
# - UUID (hex)
KebabSnakeRegex = re.compile(r"^[a-z0-9]+(?:[-_][a-z0-9]+)*$")
UUIDv4Regex = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)


def _is_valid_widget_id(value: str) -> bool:
    if not isinstance(value, str):
        return False
    if not value.strip():
        return False
    if " " in value:
        return False
    # запрещаем явные пробелы/кириллицу
    try:
        value.encode("ascii")
    except UnicodeEncodeError:
        return False

    if KebabSnakeRegex.match(value):
        return True
    if UUIDv4Regex.match(value):
        return True

    return False


def test_widget_id_format_and_uniqueness(api_client, auth_header):
    """
    API CONTRACT 006

    Проверяем:
    - наличие widgets и их тип
    - наличие и тип widget.id
    - формат id (kebab_case / snake_case / uuid)
    - отсутствие пробелов, кириллицы и пустых значений
    - уникальность id по всему manifest
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

    assert isinstance(data, dict), "Корневой объект manifest должен быть объектом JSON"

    assert "widgets" in data, "В manifest отсутствует обязательное поле 'widgets'"
    widgets = data["widgets"]
    assert isinstance(widgets, list), "'widgets' должен быть массивом"

    assert widgets, "Список widgets не должен быть пустым"

    seen_ids = set()

    for idx, widget in enumerate(widgets):
        assert isinstance(widget, dict), f"widget[{idx}] должен быть объектом JSON"

        assert "id" in widget, f"В widget[{idx}] отсутствует поле 'id'"
        wid = widget["id"]

        assert isinstance(wid, str), f"widget[{idx}].id должен быть строкой"
        stripped = wid.strip()
        assert stripped, f"widget[{idx}].id не должен быть пустой строкой"
        assert stripped == wid, f"widget[{idx}].id не должен содержать ведущих/замыкающих пробелов"

        assert _is_valid_widget_id(wid), (
            f"widget[{idx}].id={wid!r} не соответствует допустимым форматам "
            "(kebab-case, snake_case или UUID из латинских символов/цифр без пробелов/кириллицы). "
            "Если backend вводит новый формат id, нужно обновить контракт и этот тест."
        )

        assert wid not in seen_ids, (
            f"Идентификатор виджета '{wid}' не уникален (дубликат в списке widgets)"
        )
        seen_ids.add(wid)
