import json

CONFIG_PATH = "/api/v1/user/config"


def test_put_config_with_invalid_types(mocker, api_client):
    error_body = {
        "code": "VALIDATION_ERROR",
        "message": "Invalid request body",
        "details": [
            {"field": "id", "message": "must be string"},
            {"field": "row", "message": "must be integer"},
            {"field": "col", "message": "must be integer"},
            {"field": "width", "message": "must be integer"},
        ],
        "traceId": "trace-func-009",
    }

    resp = mocker.Mock()
    resp.status_code = 400
    resp.headers = {
        "Content-Type": "application/json",
        "X-Request-ID": "trace-func-009",
        "Cache-Control": "no-store",
    }
    resp.json.return_value = error_body
    resp.text = json.dumps(error_body)

    mocker.patch("requests.put", return_value=resp)

    r = api_client.put(
        CONFIG_PATH,
        json={
            "id": 123,
            "row": "a",
            "col": False,
            "width": [],
        },
    )

    assert r.status_code == 400
    data = r.json()

    assert data["code"] == "VALIDATION_ERROR"
    assert len(data["details"]) == 4
    assert data["traceId"] == r.headers["X-Request-ID"]

    raw = r.text.lower()
    assert "<html" not in raw
    assert "stacktrace" not in raw
