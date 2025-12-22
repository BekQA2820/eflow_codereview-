import json
import uuid
from datetime import datetime

PROFILE_CREATE_PATH = "/api/v1/profiles/items"
PROFILE_GET_PATH = "/api/v1/profiles/items/{profile_id}"


def _assert_uuid(value: str):
    uuid.UUID(value)


def _assert_iso8601(value: str):
    datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_profile_create_with_minimal_fields(mocker, api_client):
    """
    PROFILE FUNC 003
    Создание профиля с минимальным набором обязательных полей
    """

    create_body = {
        "name": "Ivan",
        "surname": "Petrov",
        "phone": "+79990000001",
        "consent_processing": True,
        "consent_communication": True,
    }

    created_profile = {
        "id": str(uuid.uuid4()),
        **create_body,
        "created_at": "2025-01-01T10:00:00Z",
        "updated_at": "2025-01-01T10:00:00Z",
        "last_modified_by": "system",
    }

    def make_response(status: int, body: dict, etag: str):
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

    r_post = make_response(201, created_profile, "etag-v1")
    r_get = make_response(200, created_profile, "etag-v1")

    mocker.patch(
        "requests.request",
        side_effect=[r_post, r_get],
    )

    # -------------------------
    # CREATE
    # -------------------------
    create_resp = api_client.post(PROFILE_CREATE_PATH, json=create_body)

    assert create_resp.status_code == 201
    assert create_resp.headers["ETag"] == "etag-v1"

    body_post = create_resp.json()

    _assert_uuid(body_post["id"])
    _assert_iso8601(body_post["created_at"])
    _assert_iso8601(body_post["updated_at"])

    # -------------------------
    # GET by returned id
    # -------------------------
    profile_id = body_post["id"]

    get_resp = api_client.get(PROFILE_GET_PATH.format(profile_id=profile_id))

    assert get_resp.status_code == 200
    assert get_resp.headers["ETag"] == create_resp.headers["ETag"]

    body_get = get_resp.json()

    assert body_get == body_post
