import json
import pytest
import re

MANIFEST_PATH = "/api/v1/manifest"

XSS_PAYLOAD = "<script>alert(1)</script>"


def test_widget_title_xss_is_sanitized(mocker, api_client):
    """
    API SEC 012
    Проверка фильтрации HTML/XSS в widget.title
    """

    manifest_with_xss = {
        "widgets": [
            {
                "id": "widget-xss-title",
                "type": "mfe",
                "title": XSS_PAYLOAD,
                "position": {"row": 0, "col": 0, "width": 2},
                "visible": True,
            }
        ],
        "layout": {"rows": 1, "columns": 2, "gridType": "fixed"},
        "version": "1",
    }

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {
        "Content-Type": "application/json",
        "X-Request-ID": "trace-xss-001",
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
    # Body structure
    # -----------------------------
    data = r.json()
    assert "widgets" in data
    assert len(data["widgets"]) == 1

    widget = data["widgets"][0]
    assert widget["id"] == "widget-xss-title"
    assert "title" in widget
    assert isinstance(widget["title"], str)

    title = widget["title"].lower()

    # -----------------------------
    # Security checks
    # -----------------------------
    assert "<script" not in title
    assert "</script>" not in title
    assert "onerror" not in title
    assert "<img" not in title
    assert "<iframe" not in title

    # не допускаем raw HTML
    assert "<" not in title or "&lt;" in title
    assert ">" not in title or "&gt;" in title

    # -----------------------------
    # No deny-list leakage
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
