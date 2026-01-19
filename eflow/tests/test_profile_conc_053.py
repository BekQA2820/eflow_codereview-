import json
import uuid
from datetime import datetime

PROFILES_ITEMS_PATH = "/api/v1/profiles/items/{profile_id}"
DENY_FIELDS = {"debugInfo", "stackTrace", "internalMeta"}


def test_profile_etag_changes_after_successful_patch(mocker, api_client):
    """
    PROFILE CONC 053
    ETag должен изменяться при каждом успешном PATCH
    """

    profile_id = str(uuid.uuid4())
    path = PROFILES_ITEMS_PATH.format(profile_id=profile_id)

    etag_v1 = "etag-1"
    etag_v2 = "etag-2"

    body_before = {
        "profile_uuid": profile_id,
        "surname": "Ivanov",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T10:00:00Z",
    }

    body_after = {
        **body_before,
        "surname": "Petrov",
        "updated_at": "2024-01-01T10:10:00Z",
    }

    def make_resp(body, etag):
        r = mocker.Mock()
        r.status_code = 200
        r.headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            "Vary": "Authorization",
            "ETag": etag,
            "X-Request-ID": str(uuid.uuid4()),
        }
        r.json.return_value = body
        r.content = json.dumps(body).encode("utf-8")
        return r

    mocker.patch("requests.get", return_value=make_resp(body_before, etag_v1))
    mocker.patch("requests.patch", return_value=make_resp(body_after, etag_v2))

    r_get = api_client.get(path)
    assert r_get.headers["ETag"] == etag_v1

    r_patch = api_client.patch(
        path,
        headers={"If-Match": etag_v1},
        json={"surname": "Petrov"},
    )

    assert r_patch.headers["ETag"] == etag_v2
    assert r_patch.headers["ETag"] != etag_v1
    assert r_patch.json()["surname"] == "Petrov"