import json
import uuid
import pytest


MANIFEST_PATH = "/api/v1/manifest"


def test_layout_invariant_when_widgets_change(mocker, api_client):

    widgets_v1 = {
        "widgets": [
            {"id": "a", "type": "mfe", "position": {"row": 0, "col": 0, "width": 1}}
        ]
    }

    widgets_v2 = {
        "widgets": [
            {"id": "b", "type": "mfe", "position": {"row": 0, "col": 0, "width": 1}},
            {"id": "c", "type": "link", "position": {"row": 0, "col": 1, "width": 1}},
        ]
    }

    # layout должен быть одинаковым в обеих версиях
    layout_stub = {"rows": 1, "columns": 2, "gridType": "fixed"}

    manifest_v1 = {
        "widgets": widgets_v1["widgets"],
        "layout": layout_stub,
        "version": "1.0",
    }

    manifest_v2 = {
        "widgets": widgets_v2["widgets"],
        "layout": layout_stub,
        "version": "1.1",
    }

    # -------------------------------------------------
    # 2. Готовим два детерминированных HTTP-ответа
    # -------------------------------------------------
    def make_response(body, x_cache):
        mock = mocker.Mock()
        mock.status_code = 200
        mock.headers = {
            "Content-Type": "application/json",
            "X-Cache": x_cache,
            "X-Request-ID": str(uuid.uuid4()),
        }
        mock.content = json.dumps(body).encode("utf-8")
        mock.json.return_value = body
        return mock

    r1 = make_response(manifest_v1, "MISS")
    r2 = make_response(manifest_v2, "MISS")   # widgets изменились → MISS корректен

    # -------------------------------------------------
    # 3. Мокаем requests.get → возвращает v1, затем v2
    # -------------------------------------------------
    mock_get = mocker.patch("requests.get")
    mock_get.side_effect = [r1, r2]

    # -------------------------------------------------
    # 4. Первый запрос — widgets=v1
    # -------------------------------------------------
    resp1 = api_client.get(MANIFEST_PATH)

    assert resp1.status_code == 200
    assert resp1.headers.get("Content-Type") == "application/json"
    assert "X-Request-ID" in resp1.headers
    data1 = resp1.json()
    assert isinstance(data1, dict)

    assert "layout" in data1 and isinstance(data1["layout"], dict)
    assert "widgets" in data1 and isinstance(data1["widgets"], list)

    layout_before = data1["layout"]

    # -------------------------------------------------
    # 5. Второй запрос — widgets=v2
    # -------------------------------------------------
    resp2 = api_client.get(MANIFEST_PATH)

    assert resp2.status_code == 200
    assert resp2.headers.get("Content-Type") == "application/json"
    assert "X-Request-ID" in resp2.headers

    data2 = resp2.json()

    # -------------------------------------------------
    # 6. Проверяем: layout НЕ изменился
    # -------------------------------------------------
    layout_after = data2["layout"]

    assert layout_before == layout_after, \
        f"Layout должен оставаться инвариантным при изменении widgets, но отличается:\n" \
        f"before={layout_before}\nafter={layout_after}"

    # -------------------------------------------------
    # 7. Widgets должны измениться
    # -------------------------------------------------
    assert data1["widgets"] != data2["widgets"], \
        "Ожидали изменение widgets при новой версии S3"

    # -------------------------------------------------
    # 8. Убедимся, что requests.get был вызван дважды
    # -------------------------------------------------
    assert mock_get.call_count == 2
