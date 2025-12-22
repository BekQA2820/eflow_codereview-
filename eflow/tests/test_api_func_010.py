import json

CONFIG_PATH = "/api/v1/user/config"


def test_put_config_with_unexpected_field(mocker, api_client):
    error_body = {
        "code": "VALIDATION_ERROR",
        "message": "Unexpected field",
        "details": [
            {
                "field": "unexpected",
                "message": "field is not allowed",
            }
        ],
        "traceId": "trace-func-010",
    }

    resp = mocker.Mock()
    resp.status_code = 400
    resp.headers = {
        "Content-Type": "application/json",
        "X-Request-ID": "trace-func-010",
        "Cache-Control": "no-store",
    }
    resp.json.return_value = error_body
    resp.text = json.dumps(error_body)

    mocker.patch("requests.put", return_value=resp)

    r = api_client.put(
        CONFIG_PATH,
        json={
            "id": "widget-1",
            "row": 0,
            "col": 0,
            "width": 3,
            "unexpected": 123,
        },
    )

    assert r.status_code == 400
    data = r.json()

    assert data["code"] == "VALIDATION_ERROR"
    assert data["traceId"] == r.headers["X-Request-ID"]

    raw = r.text.lower()
    assert "<html" not in raw
    assert "stacktrace" not in raw
