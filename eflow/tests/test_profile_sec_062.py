import json
import uuid

DENY_FIELDS = {"debugInfo", "stackTrace", "internalMeta"}


def test_profile_token_expired(mocker, api_client):
    """
    PROFILE SEC 062
    Просроченный access token
    """

    trace_id = str(uuid.uuid4())

    error_body = {
        "code": "TOKEN_EXPIRED",
        "message": "Access token expired",
        "details": [],
        "traceId": trace_id,
    }

    resp = mocker.Mock()
    resp.status_code = 401
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "X-Request-ID": trace_id,
    }
    resp.json.return_value = error_body
    resp.content = json.dumps(error_body).encode("utf-8")

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(
        "/api/v1/profiles/items/any-id",
        headers={"Authorization": "Bearer expired.token.value"},
    )

    assert r.status_code == 401
    assert r.headers["Content-Type"] == "application/json"

    data = r.json()
    assert data["code"] == "TOKEN_EXPIRED"
    assert data["traceId"] == r.headers["X-Request-ID"]

    for f in DENY_FIELDS:
        assert f not in data