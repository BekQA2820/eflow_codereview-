import json

MANIFEST_PATH = "/api/v1/manifest"


def test_error_response_403_forbidden_is_sanitized(mocker, api_client):
    """
    API SEC 010
    Корректный ErrorResponse для 403 без HTML и внутренних полей
    """

    error_body = {
        "code": "FORBIDDEN",
        "message": "Access denied",
        "details": [],
        "traceId": "trace-403",
    }

    resp = mocker.Mock()
    resp.status_code = 403
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "X-Request-ID": "trace-403",
        "Vary": "Authorization",
    }
    resp.json.return_value = error_body
    resp.text = json.dumps(error_body)

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(
        MANIFEST_PATH,
        headers={"Authorization": "Bearer employee-token"},
    )

    assert r.status_code == 403
    assert r.headers["Content-Type"].startswith("application/json")
    assert "public" not in r.headers.get("Cache-Control", "")

    body = r.json()
    assert set(body.keys()) == {"code", "message", "details", "traceId"}
    assert body["code"] == "FORBIDDEN"
    assert body["traceId"] == r.headers["X-Request-ID"]

    raw = r.text.lower()
    assert "<html" not in raw
    assert "stacktrace" not in raw
    assert "exception" not in raw
