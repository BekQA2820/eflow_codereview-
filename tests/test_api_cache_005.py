import json
import uuid
import pytest

MANIFEST_PATH = "/api/v1/manifest"


def test_manifest_etag_and_304_handling(mocker, api_client):

    manifest_body = {
        "widgets": [{"id": "x"}],
        "layout": {"rows": 1, "columns": 2, "gridType": "fixed"},
        "version": "1.0"
    }

    encoded_body = json.dumps(manifest_body).encode("utf-8")
    etag_value = '"abc123etag"'  # RFC: ETag — всегда строка в кавычках

    # ---------------------------------
    # 1. Первый ответ — 200 OK (ETag)
    # ---------------------------------
    r1 = mocker.Mock()
    r1.status_code = 200
    r1.headers = {
        "Content-Type": "application/json",
        "ETag": etag_value,
        "Cache-Control": "max-age=300",
        "X-Request-ID": str(uuid.uuid4()),
    }
    r1.content = encoded_body
    r1.json.return_value = manifest_body

    # ---------------------------------
    # 2. Второй ответ — 304 Not Modified
    # ---------------------------------
    r2 = mocker.Mock()
    r2.status_code = 304
    r2.headers = {
        "ETag": etag_value,            # RFC: обязателен при 304
        "Cache-Control": "max-age=300",
        "X-Request-ID": str(uuid.uuid4()),
    }
    r2.content = b""                  # RFC: тело отсутствует
    r2.json.side_effect = ValueError("304 has no JSON body")

    # ---------------------------------
    # 3. Мокаем requests.get: 200 → 304
    # ---------------------------------
    mock_get = mocker.patch("requests.get", side_effect=[r1, r2])

    # ---------------------------------
    # 4. Первый запрос — должен вернуть 200
    # ---------------------------------
    response_200 = api_client.get(MANIFEST_PATH)

    assert response_200.status_code == 200

    assert response_200.headers.get("Content-Type") == "application/json", \
        "Ответ 200 обязан быть JSON"

    assert "ETag" in response_200.headers, "ETag обязателен в 200 OK"
    assert response_200.headers["ETag"] == etag_value, "ETag должен быть корректным"

    assert response_200.content == encoded_body, "Тело 200 должно быть корректным JSON"
    parsed_200 = response_200.json()
    assert isinstance(parsed_200, dict)

    # ---------------------------------
    # 5. Второй запрос — If-None-Match → 304
    # ---------------------------------
    response_304 = api_client.get(
        MANIFEST_PATH,
        headers={"If-None-Match": etag_value}
    )

    assert response_304.status_code == 304, \
        f"Ожидаем 304, получили {response_304.status_code}"

    # RFC7232: тело при 304 отсутствует
    assert response_304.content in (b"", None), \
        "304 Not Modified не должен возвращать тело"

    # RFC: ETag обязателен
    assert "ETag" in response_304.headers, "304 обязан содержать ETag"
    assert response_304.headers["ETag"] == etag_value, \
        "ETag при 304 обязан совпадать с первоначальным"

    # Cache-Control также обязателен
    assert "Cache-Control" in response_304.headers, \
        "304 обязан содержать Cache-Control"

    # X-Request-ID должен быть
    assert "X-Request-ID" in response_304.headers

    # ---------------------------------
    # 6. Проверяем, что backend вызван дважды
    # ---------------------------------
    assert mock_get.call_count == 2
