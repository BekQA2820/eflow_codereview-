# tests/test_api_sec_012.py

import json
import pytest

MANIFEST_PATH = "/api/v1/manifest"

XSS_PAYLOAD = "<script>alert(1)</script>"


def test_widget_title_xss_is_sanitized(mocker, api_client):
    """
    API SEC 012
    Widget title must not contain raw HTML or executable JS
    """

    sanitized_title = "alert(1)"

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {
        "Content-Type": "application/json",
        "X-Request-ID": "trace-xss-001",
        "Cache-Control": "no-store",
    }
    resp.json.return_value = {
        "widgets": [
            {
                "id": "widget-xss-title",
                "type": "mfe",
                "title": sanitized_title,
                "position": {"row": 0, "col": 0, "width": 2},
                "visible": True,
            }
        ],
        "layout": {"rows": 1, "columns": 2, "gridType": "fixed"},
        "version": "1",
    }
    resp.text = json.dumps(resp.json.return_value)

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(MANIFEST_PATH)
    data = r.json()
    title = data["widgets"][0]["title"].lower()

    assert "<script" not in title
    assert "<" not in title
    assert ">" not in title
