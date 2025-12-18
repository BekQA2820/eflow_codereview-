import json
import uuid


PROFILE_PATH = "/api/v1/profiles/items/{profile_id}"


def _assert_uuid(value: str):
    uuid.UUID(value)


def test_profile_concurrent_update_with_etag(mocker, api_client):
    """
    PROFILE CONC 007
    Оптимистичная блокировка через ETag и If-Match
    """

    profile_id = str(uuid.uuid4())
    etag_v1 = "etag-v1"
    etag_v2 = "etag-v2"

    base_profile = {
        "id": profile_id,
        "name": "Ivan",
        "surname": "Petrov",
        "phone": "+79990000001",
        "created_at": "2025-01-01T10:00:00Z",
        "updated_at": "2025-01-01T10:00:00Z",
        "last_modified_by": "system",
    }

    updated_profile = {
        **base_profile,
        "name": "Petr",
        "updated_at": "2025-01-01T10:05:00Z",
        "last_modified_by": "user-a",
    }

    def make_response(status, body, etag):
        resp = mocker.Mock()
        resp.status_code = status
        resp.headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            "Vary": "Authorization",
            "ETag": etag,
            "X-Request-ID": str(uuid.uuid4()),
        }
        resp.json.return_value = body
        resp.content = json.dumps(body).encode("utf-8")
        return resp

    r_get = make_response(200, base_profile, etag_v1)
    r_patch_ok = make_response(200, updated_profile, etag_v2)

    r_patch_conflict = mocker.Mock()
    r_patch_conflict.status_code = 412
    r_patch_conflict.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "X-Request-ID": str(uuid.uuid4()),
    }
    r_patch_conflict.json.return_value = {
        "code": "ETAG_MISMATCH",
        "message": "ETag mismatch",
        "details": [],
        "traceId": r_patch_conflict.headers["X-Request-ID"],
    }
    r_patch_conflict.content = json.dumps(
        r_patch_conflict.json.return_value
    ).encode("utf-8")

    mocker.patch(
        "requests.request",
        side_effect=[r_get, r_patch_ok, r_patch_conflict],
    )

    # GET
    r1 = api_client.get(PROFILE_PATH.format(profile_id=profile_id))
    assert r1.headers["ETag"] == etag_v1

    # PATCH A
    r2 = api_client.patch(
        PROFILE_PATH.format(profile_id=profile_id),
        headers={"If-Match": etag_v1},
        json={"name": "Petr"},
    )

    assert r2.status_code == 200
    assert r2.headers["ETag"] == etag_v2
    assert r2.json()["name"] == "Petr"

    # PATCH B with old ETag
    r3 = api_client.patch(
        PROFILE_PATH.format(profile_id=profile_id),
        headers={"If-Match": etag_v1},
        json={"surname": "Ivanov"},
    )

    assert r3.status_code == 412
    body = r3.json()

    assert body["traceId"] == r3.headers["X-Request-ID"]
    _assert_uuid(body["traceId"])