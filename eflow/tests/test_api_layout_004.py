import json
import pytest

MANIFEST_PATH = "/api/v1/manifest"


def make_response(mocker, body):
    r = mocker.Mock()
    r.status_code = 200
    r.headers = {
        "Content-Type": "application/json",
        "ETag": "a" * 32,
        "Cache-Control": "private, max-age=300",
        "X-Cache": "HIT",
        "X-Request-ID": "req-id",
    }
    r.json.return_value = body
    r.text = json.dumps(body)
    return r


def test_layout_and_widgets_order_is_deterministic(mocker, api_client):
    """
    API LAYOUT 004
    Layout и порядок widgets должны быть полностью детерминированны
    """

    manifest = {
        "layout": {"rows": 2, "columns": 3, "gridType": "fixed"},
        "widgets": [
            {"id": "a", "type": "mfe", "position": {"row": 0, "col": 0, "width": 1}},
            {"id": "b", "type": "link", "position": {"row": 0, "col": 1, "width": 1}},
            {"id": "c", "type": "mfe", "position": {"row": 1, "col": 0, "width": 2}},
        ],
    }

    r1 = make_response(mocker, manifest)
    r2 = make_response(mocker, manifest)
    r3 = make_response(mocker, manifest)

    mocker.patch("requests.get", side_effect=[r1, r2, r3])

    responses = [
        api_client.get(MANIFEST_PATH),
        api_client.get(MANIFEST_PATH),
        api_client.get(MANIFEST_PATH),
    ]

    for resp in responses:
        assert resp.status_code == 200
        assert resp.headers.get("Content-Type") == "application/json"

        raw = resp.text.lower()
        assert "<html" not in raw
        assert "stacktrace" not in raw

    widgets_orders = [
        [w["id"] for w in resp.json()["widgets"]] for resp in responses
    ]

    layout_snapshots = [
        resp.json()["layout"] for resp in responses
    ]

    assert widgets_orders[0] == widgets_orders[1] == widgets_orders[2], (
        f"Недетерминированный порядок widgets: {widgets_orders}"
    )

    assert layout_snapshots[0] == layout_snapshots[1] == layout_snapshots[2], (
        f"Layout отличается между запросами: {layout_snapshots}"
    )
