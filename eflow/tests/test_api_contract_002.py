import pytest
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

MANIFEST_PATH = "/api/v1/manifest"

# Строгий deny-list
DENY_FIELDS = {
    "internalFlags",
    "internalId",
    "serviceRouting",
    "debugInfo",
    "backendOnly",
    "requiredPermissions",
    "internalMeta",
    "configSource",
}


def _walk_and_check_deny_list(node, path="root"):
    """
    Рекурсивная проверка, что ни в одном узле JSON нет запрещённых внутренних полей.
    """
    if isinstance(node, dict):
        for key, value in node.items():
            assert key not in DENY_FIELDS, (
                f"Запрещённое внутреннее поле '{key}' найдено в '{path}'"
            )
            _walk_and_check_deny_list(value, f"{path}.{key}")

    elif isinstance(node, list):
        for idx, item in enumerate(node):
            _walk_and_check_deny_list(item, f"{path}[{idx}]")


def _assert_iso8601_timestamp(value: str):
    """
    Проверка формата generatedAt:
    - ISO 8601 (строгий)
    - обязательно Z (UTC)
    - время не сильно отличается от текущего (<= 5 сек)
    """
    assert isinstance(value, str) and value.strip(), "generatedAt должен быть непустой строкой"

    # Строгая проверка формата ISO 8601
    iso_regex = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
    assert re.match(iso_regex, value), (
        f"generatedAt имеет неверный формат: {value!r}. "
        f"Ожидается ISO 8601 с Z (UTC), пример: 2025-01-14T11:30:22.123Z"
    )

    # Парсинг
    dt = parsedate_to_datetime(value)
    assert dt.tzinfo is not None, "generatedAt должен иметь таймзону"
    assert dt.tzinfo == timezone.utc, "generatedAt обязан быть в UTC (заканчивается на Z)"

    # Проверка clock skew
    now = datetime.now(timezone.utc)
    delta = abs((now - dt).total_seconds())
    assert delta <= 5, (
        f"generatedAt слишком сильно отличается от текущего времени (Δ={delta:.3f}s > 5s). "
        f"Value={value}, now={now.isoformat()}"
    )


def test_manifest_matches_backend_model_contract(api_client, auth_header, manifest_schema):
    """
    API CONTRACT 002 — ПОЛНАЯ ПРОВЕРКА manifest согласно backend-модели.
    Включает:
    - обязательные поля
    - строгие типы
    - ограничение значений
    - валидацию JSON Schema
    - отсутствие внутренних полей
    - корректность generatedAt (ISO 8601 / UTC / clock skew)
    """

    # -------------------------------
    # 1. Получение ответа
    # -------------------------------
    r = api_client.get(MANIFEST_PATH, headers=auth_header)

    assert r.status_code == 200, f"Ожидаем 200 OK, получили {r.status_code}"
    ctype = r.headers.get("Content-Type", "")
    assert ctype.startswith("application/json"), (
        f"Ожидаем JSON-ответ, получено Content-Type={ctype}"
    )

    try:
        data = r.json()
    except Exception as e:
        pytest.fail(f"Ответ не является валидным JSON: {e}")

    assert isinstance(data, dict), "Корневой объект манифеста должен быть JSON-объектом"

    # -------------------------------
    # 2. Проверка обязательных полей
    # -------------------------------
    required_root = ("widgets", "layout", "gridType", "version", "generatedAt")

    for key in required_root:
        assert key in data, f"Отсутствует обязательное поле '{key}'"

    widgets = data["widgets"]
    layout = data["layout"]

    # -------------------------------
    # 3. Валидация типов верхнего уровня
    # -------------------------------
    assert isinstance(widgets, list), "'widgets' должен быть массивом"
    assert isinstance(layout, dict), "'layout' должен быть объектом"
    assert isinstance(data["gridType"], str), "'gridType' должен быть строкой"

    version = data["version"]
    assert isinstance(version, (str, int)), (
        f"'version' должен быть строкой или числом, получено {type(version).__name__}"
    )

    # -------------------------------
    # 4. generatedAt (строгая ISO 8601 / UTC / clock skew)
    # -------------------------------
    _assert_iso8601_timestamp(data["generatedAt"])

    # -------------------------------
    # 5. layout структура
    # -------------------------------
    for key in ("rows", "columns"):
        assert key in layout, f"layout должен содержать '{key}'"
        assert isinstance(layout[key], int), f"layout['{key}'] должен быть числом"
        assert layout[key] > 0, f"layout['{key}'] должен быть > 0"

    # Доп. защита: нет запрещённых полей
    for k in layout:
        assert k not in DENY_FIELDS, f"Запрещённое поле '{k}' найдено в layout"

    # -------------------------------
    # 6. widgets[]
    # -------------------------------
    assert len(widgets) > 0, "widgets не должен быть пустым"

    seen_ids = set()

    for idx, widget in enumerate(widgets):
        assert isinstance(widget, dict), f"widget[{idx}] должен быть объектом"

        # Обязательные поля
        for req in ("id", "type", "position"):
            assert req in widget, f"В widget[{idx}] отсутствует поле '{req}'"

        wid = widget["id"]
        wtype = widget["type"]
        pos = widget["position"]

        # id
        assert isinstance(wid, str), f"widget[{idx}].id должен быть строкой"
        assert wid.strip(), f"widget[{idx}].id не должен быть пустым"
        assert wid not in seen_ids, f"widget id '{wid}' дублируется"
        seen_ids.add(wid)

        # type
        assert isinstance(wtype, str), f"widget[{idx}].type должен быть строкой"

        # position
        assert isinstance(pos, dict), f"widget[{idx}].position должен быть объектом"

        for coord in ("row", "col", "width"):
            assert coord in pos, f"В widget[{idx}].position нет '{coord}'"
            assert isinstance(pos[coord], int), (
                f"widget[{idx}].position['{coord}'] должен быть числом"
            )

        assert pos["row"] >= 0, f"row < 0 у widget[{idx}]"
        assert pos["col"] >= 0, f"col < 0 у widget[{idx}]"
        assert pos["width"] >= 1, f"width < 1 у widget[{idx}]"

        # Ограничение выхода за layout
        assert pos["col"] + pos["width"] <= layout["columns"], (
            f"widget[{idx}] выходит за границы layout по ширине"
        )

        # Проверка deny-list
        _walk_and_check_deny_list(widget, f"widget[{idx}]")

    # -------------------------------
    # 7. Глобальная проверка deny-list
    # -------------------------------
    _walk_and_check_deny_list(data)

    # -------------------------------
    # 8. JSON Schema валидация
    # -------------------------------
    try:
        from jsonschema import validate
        validate(instance=data, schema=manifest_schema)
    except Exception as e:
        pytest.fail(f"JSON Schema validation failed: {e}")
