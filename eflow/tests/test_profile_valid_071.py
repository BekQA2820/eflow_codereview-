import json
import uuid
import re

UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")
DENY_FIELDS = {"debugInfo", "stackTrace", "internalMeta"}


def test_profile_accepts_valid_unicode_name(mocker, api_client):
    """
    PROFILE VALID 071
    Корректная обработка Unicode-символов в имени профиля
    """

    trace_id = str(uuid.uuid4())

    body = {
        "id": "profile-1",
        "displayName": "Иван Петрович",
        "traceId": trace_id,
    }

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "X-Request-ID": trace_id,
    }
    resp.json.return_value = body
    resp.content = json.dumps(body, ensure_ascii=False).encode("utf-8")

    mocker.patch("requests.patch", return_value=resp)

    r = api_client.patch(
        "/api/v1/profiles/items/profile-1",
        json={"displayName": "Иван Петрович"},
    )

    assert r.status_code == 200
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"
    assert UUID_RE.match(r.headers["X-Request-ID"])

    data = r.json()
    assert data["displayName"] == "Иван Петрович"
    assert data["traceId"] == r.headers["X-Request-ID"]

    for f in DENY_FIELDS:
        assert f not in data