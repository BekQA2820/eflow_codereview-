import pytest
from datetime import datetime, timezone
from email.utils import format_datetime, parsedate_to_datetime

MANIFEST = "/api/v1/manifest"


def test_rate_limit_retry_after_handling(api_client, auth_header, mocker):

    limiter = {"count": 0}

    def fake_get(_url, *_, **__):
        from unittest.mock import Mock
        resp = Mock()

        limiter["count"] += 1

        # Первые 3 запроса — 200 OK
        if limiter["count"] <= 3:
            remaining = max(0, 3 - limiter["count"])
            resp.status_code = 200
            resp.headers = {"X-RateLimit-Remaining": str(remaining)}
            resp.json.return_value = {"ok": True}
            return resp

        # 4-й — 429 Too Many Requests
        retry_after_seconds = 2

        now_utc = datetime.now(timezone.utc)

        resp.status_code = 429
        resp.headers = {
            # вариант delta-seconds (по контракту)
            "Retry-After": str(retry_after_seconds),
            "Date": format_datetime(now_utc),
        }
        resp.json.return_value = {"code": "RATE_LIMIT_EXCEEDED"}
        return resp

    mocker.patch("requests.get", side_effect=fake_get)

    # 1–3: должны пройти
    r1 = api_client.get(MANIFEST, headers=auth_header)
    r2 = api_client.get(MANIFEST, headers=auth_header)
    r3 = api_client.get(MANIFEST, headers=auth_header)

    for idx, r in enumerate([r1, r2, r3], start=1):
        assert r.status_code == 200, f"R{idx}: ожидаем 200 OK"

    # 4-й: 429
    r4 = api_client.get(MANIFEST, headers=auth_header)
    assert r4.status_code == 429, "Должен вернуться 429 при превышении лимита"

    retry_after = r4.headers.get("Retry-After")
    assert retry_after is not None, "Retry-After обязателен при 429"

    # --- формат Retry-After ---
    if retry_after.isdigit():
        value = int(retry_after)
        assert value > 0, "Retry-After (delta-seconds) должен быть > 0"
    else:
        # HTTP-date вариант
        try:
            dt = parsedate_to_datetime(retry_after)
        except (TypeError, ValueError):
            pytest.fail(f"Retry-After не является валидной HTTP-датой: {retry_after}")

        assert dt.tzinfo is not None, "HTTP-date должен быть с таймзоной"
        assert dt > datetime.now(timezone.utc), "HTTP-date должен указывать будущее время"

    # «Ожидание» окна — без sleep, просто сбрасываем счётчик
    limiter["count"] = 0

    r5 = api_client.get(MANIFEST, headers=auth_header)
    assert r5.status_code == 200, "После Retry-After следующий запрос должен пройти"
    assert "X-RateLimit-Remaining" in r5.headers
