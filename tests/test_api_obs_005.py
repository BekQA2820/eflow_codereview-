import json

MANIFEST_PATH = "/api/v1/manifest"


def test_trace_id_matches_x_request_id_on_error(mocker, api_client):
    error_body = {
        "code": "VALIDATION_ERROR",
        "message": "Invalid limit",
        "details": [],
        "traceId": "trace-obs-005",
    }

    resp = mocker.Mock()
    resp.status_code = 400
    resp.headers = {
        "Content-Type": "application/json",
        "X-Request-ID": "trace-obs-005",
        "Cache-Control": "no-store",
    }
    resp.json.return_value = error_body
    resp.text = json.dumps(error_body)

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(f"{MANIFEST_PATH}?limit=invalid")

    assert r.status_code == 400
    assert r.headers["Content-Type"].startswith("application/json")

    data = r.json()
    assert set(data.keys()) == {"code", "message", "details", "traceId"}
    assert data["traceId"] == r.headers["X-Request-ID"]

    raw = r.text.lower()
    assert "<html" not in raw
    assert "stacktrace" not in raw
