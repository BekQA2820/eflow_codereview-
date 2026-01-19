import json
import uuid
import re


def _assert_uuid(v: str):
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        v,
    )


def test_profile_cache_015_authorization_affects_cache(mocker, api_client):
    """
    PROFILE CACHE 015
    Ответ профиля кэшируется с учётом Authorization
    """

    trace_a = str(uuid.uuid4())
    trace_b = str(uuid.uuid4())

    body_a = {
        "profileId": "user-a",
        "displayName": "User A",
    }

    body_b = {
        "profileId": "user-b",
        "displayName": "User B",
    }

    def make_resp(body, trace_id):
        r = mocker.Mock()
        r.status_code = 200
        r.headers = {
            "Content-Type": "application/json",
            "Cache-Control": "private, max-age=60",
            "Vary": "Authorization",
            "ETag": f'"{uuid.uuid4()}"',
            "X-Request-ID": trace_id,
        }
        r.json.return_value = body
        r.content = json.dumps(body).encode("utf-8")
        return r

    resp_a = make_resp(body_a, trace_a)
    resp_b = make_resp(body_b, trace_b)

    mocker.patch("requests.get", side_effect=[resp_a, resp_b])

    # ---------- User A ----------
    r1 = api_client.get(
        "/api/v1/profiles/me",
        headers={"Authorization": "Bearer token-a"},
    )

    assert r1.status_code == 200
    assert r1.headers["Content-Type"] == "application/json"
    assert r1.headers["Vary"] == "Authorization"

    body1 = r1.json()
    assert body1["profileId"] == "user-a"
    assert body1["displayName"] == "User A"

    _assert_uuid(r1.headers["X-Request-ID"])

    # ---------- User B ----------
    r2 = api_client.get(
        "/api/v1/profiles/me",
        headers={"Authorization": "Bearer token-b"},
    )

    assert r2.status_code == 200
    assert r2.headers["Content-Type"] == "application/json"
    assert r2.headers["Vary"] == "Authorization"

    body2 = r2.json()
    assert body2["profileId"] == "user-b"
    assert body2["displayName"] == "User B"

    _assert_uuid(r2.headers["X-Request-ID"])

    # ---------- Cache safety ----------
    assert body1 != body2
    assert r1.headers["ETag"] != r2.headers["ETag"]