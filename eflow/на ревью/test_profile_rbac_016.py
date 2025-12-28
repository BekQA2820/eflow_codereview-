import json
import uuid
import re


def _assert_uuid(v: str):
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        v,
    )


def test_profile_rbac_016_access_denied_for_foreign_profile(mocker, api_client):
    """
    PROFILE RBAC 016
    Пользователь не может читать профиль, к которому не имеет прав
    """

    trace_id = str(uuid.uuid4())

    error_body = {
        "code": "ACCESS_DENIED",
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
    resp.json.return_value = error_body
    resp.content = json.dumps(error_body).encode("utf-8")

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(
        "/api/v1/profiles/items/foreign-profile-id",
        headers={"Authorization": "Bearer token-user"},
    )

    assert r.status_code == 403
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Vary"] == "Authorization"

    body = r.json()
    assert set(body.keys()) == {"code", "message", "details", "traceId"}
    assert body["code"] == "ACCESS_DENIED"
    assert body["traceId"] == r.headers["X-Request-ID"]

    _assert_uuid(body["traceId"])