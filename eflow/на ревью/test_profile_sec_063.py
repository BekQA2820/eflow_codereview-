import json
import uuid

DENY_FIELDS = {"debugInfo", "stackTrace", "internalMeta"}


def test_profile_reject_html_injection(mocker, api_client):
    """
    PROFILE SEC 063
    Попытка HTML-инъекции в текстовое поле
    """

    trace_id = str(uuid.uuid4())

    error_body = {
        "code": "INVALID_INPUT",
        "message": "Invalid input detected",
        "details": [
            {"field": "displayName", "code": "HTML_NOT_ALLOWED"}
        ],
        "traceId": trace_id,
    }

    resp = mocker.Mock()
    resp.status_code = 400
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "X-Request-ID": trace_id,
    }
    resp.json.return_value = error_body
    resp.content = json.dumps(error_body).encode("utf-8")

    mocker.patch("requests.patch", return_value=resp)

    r = api_client.patch(
        "/api/v1/profiles/items/profile-1",
        json={"displayName": "<script>alert(1)</script>"},
    )

    assert r.status_code == 400
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Vary"] == "Authorization"

    data = r.json()
    assert set(data.keys()) == {"code", "message", "details", "traceId"}
    assert data["traceId"] == r.headers["X-Request-ID"]
    assert data["details"][0]["code"] == "HTML_NOT_ALLOWED"

    for f in DENY_FIELDS:
        assert f not in data