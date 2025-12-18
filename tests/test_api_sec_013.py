import json


MANIFEST_PATH = "/api/v1/manifest"

XSS_PAYLOAD = '<img src=x onerror=alert(1)>'


def test_widget_description_xss_is_sanitized(mocker, api_client):
    """
    API SEC 013
    Проверка фильтрации HTML/XSS в widget.description
    """

    manifest_with_xss = {
        "widgets": [
            {
                "id": "widget-xss-desc",
                "type": "mfe",
                "description": XSS_PAYLOAD,
                "position": {"row": 1, "col": 0, "width": 3},
                "visible": True,
            }
        ],
        "layout": {"rows": 2, "columns": 3, "gridType": "fixed"},
        "version": "1",
    }

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {
        "Content-Type": "application/json",
        "X-Request-ID": "trace-xss-desc-001",
        "Cache-Control": "no-store",
    }
    resp.json.return_value = manifest_with_xss
    resp.text = json.dumps(manifest_with_xss)

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(MANIFEST_PATH)

    # -----------------------------
    # HTTP
    # -----------------------------
    assert r.status_code == 200
    assert r.headers["Content-Type"].startswith("application/json")

    # -----------------------------
    # Body
    # -----------------------------
    data = r.json()
    assert "widgets" in data
    assert len(data["widgets"]) == 1

    widget = data["widgets"][0]
    assert widget["id"] == "widget-xss-desc"
    assert "description" in widget
    assert isinstance(widget["description"], str)

    desc = widget["description"].lower()

    # -----------------------------
    # XSS hardening
    # -----------------------------
    assert "<img" not in desc
    assert "onerror" not in desc
    assert "<script" not in desc
    assert "javascript:" not in desc
    assert "data:" not in desc

    # запрещаем сырой HTML
    assert "<" not in desc or "&lt;" in desc
    assert ">" not in desc or "&gt;" in desc

    # -----------------------------
    # No internal leakage
    # -----------------------------
    raw = r.text.lower()
    deny_fields = {
        "internalflags",
        "internalid",
        "debuginfo",
        "backendonly",
        "servicerouting",
        "internalmeta",
        "configsource",
    }

    for field in deny_fields:
        assert field not in raw
