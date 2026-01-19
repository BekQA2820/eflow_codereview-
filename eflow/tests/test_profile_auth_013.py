import json
import uuid
import re


def _assert_uuid(v: str):
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        v,
    )


def test_profile_auth_013_expired_token_rejected(mocker, api_client):
    """
    PROFILE AUTH 013
    Просроченный access token отклоняется
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
        "/api/v1/profiles/me",
        headers={"Authorization": "Bearer expired.token"},
    )

    assert r.status_code == 401
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Vary"] == "Authorization"

    body = r.json()
    assert body["code"] == "TOKEN_EXPIRED"
    assert body["traceId"] == r.headers["X-Request-ID"]

    _assert_uuid(body["traceId"])