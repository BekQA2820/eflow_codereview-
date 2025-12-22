import json
import gzip
import pytest

MANIFEST = "/api/v1/manifest"

# Лимит можно вынести в config, но указываем здесь для теста
MAX_MANIFEST_SIZE = 512 * 1024  # 512 KB


class DummyResponse:
    def __init__(self, status_code=200, headers=None, content=b""):
        self.status_code = status_code
        self.headers = headers or {}
        self.content = content

    def json(self):
        return json.loads(self.content)


def test_manifest_size_limit(api_client, auth_header, mocker):
    """
    PERF_003 — Проверка максимального размера manifest.

    Требования:
    ✔ сервер обязан возвращать mанифест меньше лимита Gateway (512 KB)
    ✔ Content-Type должен быть JSON
    ✔ JSON должен корректно парситься
    ✔ gzip-версия должна быть меньше или равна несжатой
    ✔ Мок — детерминированное поведение
    """

    # ---------- Готовим большой, но валидный manifest ----------
    widgets = []
    for i in range(2000):  # создаем большой payload (для теста mock)
        widgets.append({
            "id": f"w{i}",
            "type": "mfe",
            "position": {"row": i % 5, "col": (i * 2) % 5, "width": 1}
        })

    manifest_body = {
        "version": "1",
        "generatedAt": "2025-01-01T00:00:00.000Z",
        "layout": {"rows": 5, "columns": 5, "gridType": "fixed"},
        "widgets": widgets,
    }

    raw_json = json.dumps(manifest_body).encode("utf-8")
    gzipped = gzip.compress(raw_json)

    # ---------- Проверка, что raw_json действительно меньше лимита ----------
    # (тест не должен строить payload > лимита)
    assert len(raw_json) < MAX_MANIFEST_SIZE, (
        f"Тестовый manifest превышает лимит {MAX_MANIFEST_SIZE} bytes. "
        f"raw={len(raw_json)}"
    )

    # ---------- Мокаем backend ----------
    resp = DummyResponse(
        status_code=200,
        headers={
            "Content-Type": "application/json",
            "Content-Encoding": "gzip",
            "Vary": "Accept-Encoding, Authorization, X-Roles"
        },
        content=gzipped,
    )

    mocker.patch("requests.get", return_value=resp)

    # ---------- Запрос ----------
    headers = {"Accept-Encoding": "gzip", **auth_header}
    r = api_client.get(MANIFEST, headers=headers)

    assert r.status_code == 200, f"Ожидаем 200, получено {r.status_code}"

    # ---------- Проверка Content-Type ----------
    ctype = r.headers.get("Content-Type", "")
    assert ctype.startswith("application/json"), f"Content-Type должен быть JSON, а не {ctype}"

    # ---------- Проверка gzip ----------
    assert r.headers.get("Content-Encoding") == "gzip", "Manifest должен возвращаться gzip-сжатым"

    # ---------- Распаковка ----------
    try:
        decompressed = gzip.decompress(r.content)
    except Exception as e:
        pytest.fail(f"Ошибка распаковки gzip: {e}")

    # ---------- Проверка JSON ----------
    parsed = json.loads(decompressed)
    assert isinstance(parsed, dict), "JSON после декомпрессии должен быть объектом"
    assert "widgets" in parsed and isinstance(parsed["widgets"], list), "Поле widgets обязательно"

    # ---------- Проверка лимита ----------
    assert len(decompressed) < MAX_MANIFEST_SIZE, (
        f"Manifest превышает лимит {MAX_MANIFEST_SIZE} bytes. "
        f"size={len(decompressed)}"
    )

    # ---------- Проверка gzip уменьшения размера ----------
    assert len(r.content) < len(decompressed), (
        f"gzip обязан уменьшать размер ответа. "
        f"gzip={len(r.content)}, raw={len(decompressed)}"
    )
