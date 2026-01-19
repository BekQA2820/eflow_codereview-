import json
import uuid
import pytest

PROFILES_ITEMS_PATH = "/api/v1/profiles/items/{profile_id}"
DENY_FIELDS = {"debugInfo", "stackTrace", "internalMeta"}


def test_profile_validation_error_missing_required_field(mocker, api_client):
    """
    PROFILE VALID 052
    Отсутствие обязательного поля - строгий ErrorResponse
    """

    profile_id = str(uuid.uuid4())
    path = PROFILES_ITEMS_PATH.format(profile_id=profile_id)

    trace_id = str(uuid.uuid4())

    error_body = {
        "code": "VALIDATION_ERROR",
        "message": "Validation failed",
        "details": [
            {"field": "email", "code": "REQUIRED"},
        ],
        "traceId": trace_id,
    }

    resp = mocker.Mock()
    resp.status_code = 400
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "X-Request-ID": trace_id,
    }
    resp.json.return_value = error_body
    resp.content = json.dumps(error_body).encode("utf-8")

    mocker.patch("requests.post", return_value=resp)

    r = api_client.post(
        "/api/v1/profiles",
        json={"name": "Ivan"},
    )

    assert r.status_code == 400
    assert r.headers["Content-Type"] == "application/json"

    data = r.json()
    assert data["traceId"] == r.headers["X-Request-ID"]
    assert data["details"][0] == {"field": "email", "code": "REQUIRED"}

    for f in DENY_FIELDS:
        assert f not in data