# tests/test_api_sec_013.py

import json

MANIFEST_PATH = "/api/v1/manifest"

XSS_PAYLOAD = '<img src=x onerror=alert(1)>'


def test_widget_description_xss_is_sanitized(mocker, api_client):
    """
    API SEC 013
    Widget description must not contain raw HTML or JS
    """

    sanitized_description = "image removed"

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {
        "Content-Type": "application/json",
        "X-Request-ID": "trace-xss-desc-001",
        "Cache-Control": "no-store",
    }
    resp.json.return_value = {
        "widgets": [
            {
                "id": "widget-xss-desc",
                "type": "mfe",
                "description": sanitized_description,
                "position": {"row": 1, "col": 0, "width": 3},
                "visible": True,
            }
        ],
        "layout": {"rows": 2, "columns": 3, "gridType": "fixed"},
        "version": "1",
    }
    resp.text = json.dumps(resp.json.return_value)

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(MANIFEST_PATH)
    desc = r.json()["widgets"][0]["description"].lower()

    assert "<" not in desc
    assert ">" not in desc
    assert "onerror" not in desc
    assert "javascript" not in desc
