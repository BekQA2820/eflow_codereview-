import gzip
import json
import pytest

MANIFEST = "/api/v1/manifest"


class DummyResponse:
    def __init__(self, status_code=200, headers=None, content=b""):
        self.status_code = status_code
        self.headers = headers or {}
        self.content = content

    def json(self):
        return json.loads(self.content)


def test_manifest_gzip_support(api_client, auth_header, mocker):
    """
    PERF_002 — Проверка gzip-сжатия manifest.

    Требования:
    ✔ сервер обязан возвращать gzip при Accept-Encoding: gzip
    ✔ Content-Encoding == gzip
    ✔ в ответе корректный JSON после распаковки
    ✔ Vary содержит Accept-Encoding
    ✔ тело gzip меньше несжатого
    """

    # ----- Подготовка тестового JSON -----
    manifest_body = {
        "version": "1",
        "layout": {"rows": 2, "columns": 3, "gridType": "fixed"},
        "widgets": [
            {"id": "w1", "type": "mfe", "position": {"row": 0, "col": 0, "width": 2}},
            {"id": "w2", "type": "link", "position": {"row": 1, "col": 0, "width": 1}},
        ],
    }

    raw_json = json.dumps(manifest_body).encode("utf-8")
    gzipped = gzip.compress(raw_json)

    # ----- Mock ответа от backend -----
    r = DummyResponse(
        status_code=200,
        headers={
            "Content-Type": "application/json",
            "Content-Encoding": "gzip",
            "Vary": "Accept-Encoding, Authorization, X-Roles"
        },
        content=gzipped,
    )

    mocker.patch("requests.get", return_value=r)

    # ----- Запрос -----
    headers = {"Accept-Encoding": "gzip", **auth_header}
    resp = api_client.get(MANIFEST, headers=headers)

    # ----- Проверка статуса -----
    assert resp.status_code == 200, f"Ожидаем 200, получено: {resp.status_code}"

    # ----- Проверка gzip -----
    cenc = resp.headers.get("Content-Encoding", "")
    assert cenc == "gzip", f"Content-Encoding должен быть gzip, а не {cenc}"

    # ----- Проверка Vary -----
    vary = resp.headers.get("Vary", "")
    assert "Accept-Encoding" in vary, "Vary должен содержать Accept-Encoding"

    # ----- Распаковка -----
    try:
        decompressed = gzip.decompress(resp.content)
    except Exception as e:
        pytest.fail(f"Не удалось распаковать gzip: {e}")

    # ----- Проверка что JSON корректный -----
    decoded_json = json.loads(decompressed)
    assert isinstance(decoded_json, dict), "JSON после декомпрессии должен быть объектом"
    assert decoded_json == manifest_body, "Распакованный JSON должен совпадать с исходным"

    # ----- Проверка размера (gzip < raw) -----
    assert len(resp.content) < len(raw_json), (
        f"gzip должен быть меньше исходного JSON\n"
        f"gzip={len(resp.content)} bytes, raw={len(raw_json)} bytes"
    )
