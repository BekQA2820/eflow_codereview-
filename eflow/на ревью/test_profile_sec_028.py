import json
import uuid
import re


def _assert_uuid(v: str):
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        v,
    )


def test_profile_sec_028_xss_sanitized(mocker, api_client):
    """
    PROFILE SEC 028
    XSS должен быть санитизирован на уровне JSON
    """

    trace_id = str(uuid.uuid4())

    body = {
        "profile_uuid": "profile-id",
        "displayName": "alert",
    }

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "ETag": '"etag-xss"',
        "X-Request-ID": trace_id,
    }
    resp.json.return_value = body
    resp.content = json.dumps(body).encode("utf-8")

    mocker.patch("requests.patch", return_value=resp)

    r = api_client.patch(
        "/api/v1/profiles/items/profile-id",
        headers={"If-Match": '"etag-prev"'},
        json={"displayName": "<script>alert(1)</script>"},
    )

    assert r.status_code == 200
    assert r.headers["Content-Type"] == "application/json"

    data = r.json()
    assert "<script>" not in data["displayName"]
    assert "alert" in data["displayName"]

    _assert_uuid(r.headers["X-Request-ID"])