import json
import uuid
import re

DENY_FIELDS = {"debugInfo", "stackTrace", "internalMeta"}
UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")


def test_profile_token_replay_rejected(mocker, api_client):
    """
    PROFILE SEC 068
    Повторное использование одноразового security-токена запрещено
    """

    trace_id = str(uuid.uuid4())

    error_body = {
        "code": "TOKEN_REPLAY_DETECTED",
        "message": "Security token already used",
        "details": [],
        "traceId": trace_id,
    }

    resp = mocker.Mock()
    resp.status_code = 409
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "X-Request-ID": trace_id,
    }
    resp.json.return_value = error_body
    resp.content = json.dumps(error_body).encode("utf-8")

    mocker.patch("requests.post", return_value=resp)

    r = api_client.post(
        "/api/v1/profiles/security/verify",
        json={"token": "one-time-token"},
    )

    assert r.status_code == 409
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"
    assert UUID_RE.match(r.headers["X-Request-ID"])

    data = r.json()
    assert set(data.keys()) == {"code", "message", "details", "traceId"}
    assert data["traceId"] == r.headers["X-Request-ID"]

    for f in DENY_FIELDS:
        assert f not in data