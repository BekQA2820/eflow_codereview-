import json

CONFIG_PATH = "/api/v1/user/config"


def test_put_config_with_unknown_widget_id(mocker, api_client):
    error_body = {
        "code": "WIDGET_NOT_FOUND",
        "message": "Widget not found",
        "details": [{"field": "id"}],
        "traceId": "trace-func-005",
    }

    resp = mocker.Mock()
    resp.status_code = 400
    resp.headers = {
        "Content-Type": "application/json",
        "X-Request-ID": "trace-func-005",
        "Cache-Control": "no-store",
    }
    resp.json.return_value = error_body
    resp.text = json.dumps(error_body)

    mocker.patch("requests.put", return_value=resp)

    r = api_client.put(
        CONFIG_PATH,
        json={"id": "non-existing-widget", "row": 0, "col": 0, "width": 2},
    )

    assert r.status_code == 400
    data = r.json()

    assert data["code"] == "WIDGET_NOT_FOUND"
    assert data["traceId"] == r.headers["X-Request-ID"]

    raw = r.text.lower()
    assert "<html" not in raw
    assert "stacktrace" not in raw
