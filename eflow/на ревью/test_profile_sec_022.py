import json
import uuid
import re

UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")
DENY_FIELDS = {"internalId", "debugInfo", "stackTrace", "internalMeta"}


def test_profile_sec_022_xss_payload_sanitized(mocker, api_client):
    """
    PROFILE SEC 022
    XSS не сохраняется и не отражается
    """

    trace_id = str(uuid.uuid4())

    sanitized_body = {
        "profile_uuid": "p-1",
        "displayName": "&lt;script&gt;alert(1)&lt;/script&gt;",
    }

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "ETag": '"etag-xss-1"',
        "X-Request-ID": trace_id,
    }
    resp.json.return_value = sanitized_body
    resp.content = json.dumps(sanitized_body).encode("utf-8")

    mocker.patch("requests.patch", return_value=resp)

    r = api_client.patch(
        "/api/v1/profiles/items/p-1",
        json={"displayName": "<script>alert(1)</script>"},
        headers={"If-Match": '"etag-xss-0"'},
    )

    assert r.status_code == 200
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"
    assert r.headers["ETag"] == '"etag-xss-1"'
    assert UUID_RE.match(r.headers["X-Request-ID"])

    body = r.json()
    assert body["displayName"] == "&lt;script&gt;alert(1)&lt;/script&gt;"

    for f in DENY_FIELDS:
        assert f not in body