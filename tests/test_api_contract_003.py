import pytest
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

MANIFEST_PATH = "/api/v1/manifest"

ISO_REGEX = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"


def _parse_utc(value: str) -> datetime:
    """
    Парсинг ISO 8601 timestamp в UTC с проверками.
    """
    try:
        dt = parsedate_to_datetime(value)
    except Exception as e:
        pytest.fail(f"generatedAt не удаётся распарсить как дату: {e}")

    assert dt.tzinfo is not None, "generatedAt должен содержать таймзону"
    # Нормализуем в UTC (на случай, если сервер когда-нибудь уйдёт от Z на +00:00)
    dt_utc = dt.astimezone(timezone.utc)
    return dt_utc


def test_generated_at_timestamp_format_and_freshness(api_client, auth_header):
    """
    API CONTRACT 003
    Проверка корректности generatedAt:
    - корректный ISO 8601 формат (YYYY-MM-DDTHH:mm:ss(.sss)Z)
    - UTC (Z)
    - свежесть (clock skew не больше 5 секунд)
    """

    r = api_client.get(MANIFEST_PATH, headers=auth_header)

    # Базовые HTTP проверки
    assert r.status_code == 200, f"Ожидаем 200 OK, получили {r.status_code}"
    ctype = r.headers.get("Content-Type", "")
    assert ctype.startswith("application/json"), (
        f"Ожидаем JSON-ответ, Content-Type={ctype!r}"
    )

    try:
        body = r.json()
    except Exception as e:
        pytest.fail(f"Ответ не является валидным JSON: {e}")

    assert isinstance(body, dict), "Корневой объект manifest должен быть JSON-объектом"

    # Наличие и тип поля
    assert "generatedAt" in body, "В manifest отсутствует обязательное поле 'generatedAt'"
    value = body["generatedAt"]
    assert isinstance(value, str), "generatedAt должен быть строкой"
    assert value.strip(), "generatedAt не должен быть пустой строкой"

    # Формат ISO 8601 с Z
    assert re.match(ISO_REGEX, value), (
        f"generatedAt имеет неверный формат: {value!r}. "
        "Ожидается ISO 8601 вида 'YYYY-MM-DDTHH:mm:ss(.sss)Z'"
    )

    # Семантика времени: UTC и свежесть
    dt_utc = _parse_utc(value)
    now = datetime.now(timezone.utc)
    skew = abs((now - dt_utc).total_seconds())

    assert skew <= 5, (
        f"generatedAt слишком далеко от текущего времени: Δ={skew:.3f} сек "
        f"(now={now.isoformat()}, generatedAt={dt_utc.isoformat()})"
    )
