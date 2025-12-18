import json

CONFIG_PATH = "/api/v1/user/config"


def test_put_config_with_empty_body(mocker, api_client):
    error_body = {
        "code": "VALIDATION_ERROR",
        "message": "Validation failed",
        "details": [
            {
                "field": "id",
                "message": "field is required",
            }
        ],
        "traceId": "trace-func-008",
    }

    resp = mocker.Mock()
    resp.status_code = 400
    resp.headers = {
        "Content-Type": "application/json",
        "X-Request-ID": "trace-func-008",
        "Cache-Control": "no-store",
    }
    resp.json.return_value = error_body
    resp.text = json.dumps(error_body)

    mocker.patch("requests.put", return_value=resp)

    r = api_client.put(CONFIG_PATH, json={})

    assert r.status_code == 400
    data = r.json()

    assert data["code"] == "VALIDATION_ERROR"
    assert isinstance(data["details"], list)
    assert data["traceId"] == r.headers["X-Request-ID"]

    raw = r.text.lower()
    assert "<html" not in raw
    assert "stacktrace" not in raw
