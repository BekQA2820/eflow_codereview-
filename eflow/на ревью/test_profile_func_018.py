import json
import uuid
import re


PROFILE_ITEM_PATH = "/api/v1/profiles/items/{profile_id}"


def _assert_uuid(value: str):
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        value,
    ), f"Некорректный UUID: {value}"


def test_profile_func_018_get_profile_success_contract(mocker, api_client):
    """
    PROFILE FUNC 018
    Успешное получение профиля - строгий контракт ответа
    """

    trace_id = str(uuid.uuid4())
    profile_id = "profile-123"

    body = {
        "profileId": profile_id,
        "email": "user@test.com",
        "phone": "+79990000000",
        "createdAt": "2024-01-01T10:00:00Z",
        "updatedAt": "2024-01-02T11:00:00Z",
    }

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "ETag": '"etag-v1"',
        "X-Request-ID": trace_id,
    }
    resp.json.return_value = body
    resp.content = json.dumps(body).encode("utf-8")

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(PROFILE_ITEM_PATH.format(profile_id=profile_id))

    assert r.status_code == 200
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"
    assert r.headers["ETag"] == '"etag-v1"'
    assert r.headers["X-Request-ID"] == trace_id

    data = r.json()
    assert set(data.keys()) == {
        "profileId",
        "email",
        "phone",
        "createdAt",
        "updatedAt",
    }

    assert data["profileId"] == profile_id
    _assert_uuid(r.headers["X-Request-ID"])