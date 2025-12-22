import json
import uuid
import pytest

PROFILE_PATH = "/api/v1/profiles/items/{profile_id}"
DENY_FIELDS = {"debugInfo", "internalMeta", "backendOnly", "stackTrace"}


def test_profile_rbac_read_own_profile(mocker, api_client):
    profile_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())
    etag = '"etag-v1"'

    body = {
        "id": profile_id,
        "name": "Ivan",
        "surname": "Petrov",
        "phone": "+79990000001",
    }

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "ETag": etag,
        "X-Request-ID": trace_id,
    }
    resp.json.return_value = body
    resp.content = json.dumps(body).encode("utf-8")

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(
        PROFILE_PATH.format(profile_id=profile_id),
        headers={"Authorization": "Bearer token-owner"},
    )

    assert r.status_code == 200
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"
    assert r.headers["ETag"] == etag

    data = r.json()
    assert data["id"] == profile_id
    assert data["phone"] == "+79990000001"

    assert r.headers["X-Request-ID"]
    uuid.UUID(r.headers["X-Request-ID"])

    for f in DENY_FIELDS:
        assert f not in data