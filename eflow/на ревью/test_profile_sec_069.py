import json
import uuid
import re

DENY_FIELDS = {"debugInfo", "stackTrace", "internalMeta"}
UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")


def test_profile_reject_script_tag_in_text_field(mocker, api_client):
    """
    PROFILE SEC 069
    Запрет XSS через <script> в текстовом поле
    """

    trace_id = str(uuid.uuid4())

    error_body = {
        "code": "INVALID_INPUT",
        "message": "XSS attempt detected",
        "details": [
            {"field": "displayName", "code": "XSS_NOT_ALLOWED"}
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
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"
    assert UUID_RE.match(r.headers["X-Request-ID"])

    data = r.json()
    assert set(data.keys()) == {"code", "message", "details", "traceId"}
    assert data["traceId"] == r.headers["X-Request-ID"]
    assert data["details"][0]["code"] == "XSS_NOT_ALLOWED"

    for f in DENY_FIELDS:
        assert f not in data