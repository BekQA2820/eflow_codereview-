import json
import uuid
import re


PROFILE_PATH = "/api/v1/profiles/items/{profile_id}"


def _assert_uuid(value: str):
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        value,
    )


def test_profile_rbac_013_read_other_user_profile_forbidden(mocker, api_client):
    """
    PROFILE RBAC 013
    Пользователь не может читать профиль другого пользователя
    """

    trace_id = str(uuid.uuid4())

    body = {
        "code": "FORBIDDEN",
        "message": "Access denied",
        "details": [],
        "traceId": trace_id,
    }

    resp = mocker.Mock()
    resp.status_code = 403
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "X-Request-ID": trace_id,
    }
    resp.json.return_value = body
    resp.content = json.dumps(body).encode("utf-8")

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(PROFILE_PATH.format(profile_id=" чужой-profile-id"))

    assert r.status_code == 403
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Vary"] == "Authorization"
    assert r.headers["Cache-Control"] == "no-store"

    data = r.json()
    assert set(data.keys()) == {"code", "message", "details", "traceId"}
    assert data["code"] == "FORBIDDEN"

    _assert_uuid(data["traceId"])