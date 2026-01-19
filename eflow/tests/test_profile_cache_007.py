import json
import uuid
import re


def _assert_uuid(value: str):
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        value,
    )


def test_profile_cache_007_etag_changes_after_update(mocker, api_client):
    """
    PROFILE CACHE 007
    ETag должен изменяться после PATCH обновления профиля
    """

    trace_id_get = str(uuid.uuid4())
    trace_id_patch = str(uuid.uuid4())

    get_resp = mocker.Mock()
    get_resp.status_code = 200
    get_resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "ETag": '"etag-old"',
        "X-Request-ID": trace_id_get,
    }
    get_resp.json.return_value = {"displayName": "Ivan"}
    get_resp.content = json.dumps({"displayName": "Ivan"}).encode("utf-8")

    patch_resp = mocker.Mock()
    patch_resp.status_code = 200
    patch_resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "ETag": '"etag-new"',
        "X-Request-ID": trace_id_patch,
    }
    patch_resp.json.return_value = {"displayName": "Petr"}
    patch_resp.content = json.dumps({"displayName": "Petr"}).encode("utf-8")

    mocker.patch("requests.get", return_value=get_resp)
    mocker.patch("requests.patch", return_value=patch_resp)

    r_get = api_client.get("/api/v1/profiles/items/profile-id")
    r_patch = api_client.patch(
        "/api/v1/profiles/items/profile-id",
        headers={"If-Match": r_get.headers["ETag"]},
        json={"displayName": "Petr"},
    )

    assert r_get.headers["ETag"] != r_patch.headers["ETag"]

    _assert_uuid(r_get.headers["X-Request-ID"])
    _assert_uuid(r_patch.headers["X-Request-ID"])

    assert r_patch.json()["displayName"] == "Petr"