import json
import uuid
import re


def _assert_uuid(v: str):
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        v,
    )


def test_profile_cache_011_etag_changes_after_update(mocker, api_client):
    """
    PROFILE CACHE 011
    ETag должен меняться после успешного PATCH
    """

    trace_get = str(uuid.uuid4())
    trace_patch = str(uuid.uuid4())

    body_v1 = {"profile_uuid": "profile-id", "displayName": "Ivan"}
    body_v2 = {"profile_uuid": "profile-id", "displayName": "Petr"}

    r_get = mocker.Mock()
    r_get.status_code = 200
    r_get.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "private, no-store",
        "Vary": "Authorization",
        "ETag": '"etag-v1"',
        "X-Request-ID": trace_get,
    }
    r_get.json.return_value = body_v1
    r_get.content = json.dumps(body_v1).encode("utf-8")

    r_patch = mocker.Mock()
    r_patch.status_code = 200
    r_patch.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "ETag": '"etag-v2"',
        "X-Request-ID": trace_patch,
    }
    r_patch.json.return_value = body_v2
    r_patch.content = json.dumps(body_v2).encode("utf-8")

    mocker.patch("requests.get", return_value=r_get)
    mocker.patch("requests.patch", return_value=r_patch)

    g = api_client.get("/api/v1/profiles/items/profile-id")
    etag_before = g.headers["ETag"]

    p = api_client.patch(
        "/api/v1/profiles/items/profile-id",
        headers={"If-Match": etag_before},
        json={"displayName": "Petr"},
    )

    assert p.headers["ETag"] != etag_before
    assert p.json()["displayName"] == "Petr"

    _assert_uuid(g.headers["X-Request-ID"])
    _assert_uuid(p.headers["X-Request-ID"])