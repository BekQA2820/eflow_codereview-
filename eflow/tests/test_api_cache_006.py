import json
import uuid
import pytest
from email.utils import format_datetime, parsedate_to_datetime
from datetime import datetime, timezone, timedelta

MANIFEST_PATH = "/api/v1/manifest"


def test_manifest_if_modified_since_handling(mocker, api_client):

    last_modified_dt = datetime.now(timezone.utc).replace(microsecond=0)
    last_modified_http = format_datetime(last_modified_dt)  # RFC 7231 формат

    manifest_body = {
        "widgets": [{"id": "w"}],
        "layout": {"rows": 1, "columns": 1, "gridType": "fixed"},
        "version": "1.0"
    }
    encoded_body = json.dumps(manifest_body).encode("utf-8")

    # -------------------------
    # 2. Ответ №1: 200 OK
    # -------------------------
    r1 = mocker.Mock()
    r1.status_code = 200
    r1.headers = {
        "Content-Type": "application/json",
        "Last-Modified": last_modified_http,
        "Cache-Control": "max-age=300",
        "X-Request-ID": str(uuid.uuid4()),
    }
    r1.content = encoded_body
    r1.json.return_value = manifest_body

    # -------------------------
    # 3. Ответ №2: 304 Not Modified
    # -------------------------
    r304 = mocker.Mock()
    r304.status_code = 304
    r304.headers = {
        "Last-Modified": last_modified_http,
        "Cache-Control": "max-age=300",
        "X-Request-ID": str(uuid.uuid4()),
    }
    r304.content = b""
    r304.json.side_effect = ValueError("304 has no JSON body")

    # -------------------------
    # 4. Ответ №3: 200 при будущем времени
    # -------------------------
    future_dt = last_modified_dt + timedelta(seconds=30)
    future_http_date = format_datetime(future_dt)

    r_future = mocker.Mock()
    r_future.status_code = 200
    r_future.headers = {
        "Content-Type": "application/json",
        "Last-Modified": last_modified_http,
        "Cache-Control": "max-age=300",
        "X-Request-ID": str(uuid.uuid4()),
    }
    r_future.content = encoded_body
    r_future.json.return_value = manifest_body

    # -------------------------
    # 5. Порядок ответов backend
    # -------------------------
    mock_get = mocker.patch("requests.get")
    mock_get.side_effect = [r1, r304, r_future]

    # -------------------------
    # 6. Первый запрос -> 200 OK
    # -------------------------
    resp1 = api_client.get(MANIFEST_PATH)

    assert resp1.status_code == 200
    assert resp1.headers.get("Content-Type") == "application/json"

    # Проверяем Last-Modified valid RFC 7231
    lm = resp1.headers.get("Last-Modified")
    assert lm, "Last-Modified обязателен"
    parsed = parsedate_to_datetime(lm)
    assert parsed.tzinfo is not None, "Last-Modified должен иметь timezone"
    assert parsed.tzinfo == timezone.utc, "Last-Modified должен быть в UTC"
    assert parsed <= datetime.now(timezone.utc) + timedelta(seconds=1)

    # -------------------------
    # 7. Второй запрос -> If-Modified-Since = last_modified → 304
    # -------------------------
    resp304 = api_client.get(
        MANIFEST_PATH,
        headers={"If-Modified-Since": last_modified_http}
    )

    assert resp304.status_code == 304, \
        f"Ожидаем 304 при совпадении дат, получили {resp304.status_code}"

    assert resp304.content in (b"", None), "304 не должен содержать тело"
    assert "Last-Modified" in resp304.headers, "304 обязан содержать Last-Modified"
    assert resp304.headers["Last-Modified"] == last_modified_http
    assert "Cache-Control" in resp304.headers
    assert "X-Request-ID" in resp304.headers

    # -------------------------
    # 8. Будущее время → сервер должен вернуть 200 (ресурс не «устарел»)
    # -------------------------
    resp_future = api_client.get(
        MANIFEST_PATH,
        headers={"If-Modified-Since": future_http_date}
    )

    assert resp_future.status_code == 200, \
        "На будущую дату сервер должен вернуть 200, не 304"

    assert resp_future.headers.get("Content-Type") == "application/json"
    assert resp_future.json() == manifest_body, \
        "Тело 200 при будущем timestamp должно быть валидным JSON"

    # -------------------------
    # 9. Backend вызван 3 раза
    # -------------------------
    assert mock_get.call_count == 3
