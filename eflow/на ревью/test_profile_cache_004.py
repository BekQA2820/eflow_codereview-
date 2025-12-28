import uuid
import re
import json

UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")


def test_profile_cache_004_etag_changes_after_patch(mocker, api_client):
    """
    PROFILE CACHE 004
    ETag должен изменяться после PATCH
    """

    trace_get = str(uuid.uuid4())
    trace_patch = str(uuid.uuid4())

    body_v1 = {
        "profile_uuid": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "displayName": "Ivan"
    }

    body_v2 = {
        "profile_uuid": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "displayName": "Petr"
    }

    r_get = mocker.Mock()
    r_get.status_code = 200
    r_get.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
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

    r1 = api_client.get("/api/v1/profiles/items/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    r2 = api_client.patch(
        "/api/v1/profiles/items/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        headers={"If-Match": r1.headers["ETag"]},
        json={"displayName": "Petr"}
    )

    assert r1.headers["ETag"] != r2.headers["ETag"]
    assert r2.json()["displayName"] == "Petr"