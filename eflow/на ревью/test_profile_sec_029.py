import json
import uuid
import re


DENY_FIELDS = {"debug", "stackTrace", "internal", "exception"}


def _assert_uuid(v: str):
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        v,
    )


def test_profile_sec_029_internal_fields_not_exposed(mocker, api_client):
    """
    PROFILE SEC 029
    В JSON-ответе не должно быть внутренних полей
    """

    trace_id = str(uuid.uuid4())

    body = {
        "profile_uuid": "profile-id",
        "displayName": "Ivan",
    }

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "private, no-store",
        "Vary": "Authorization",
        "X-Request-ID": trace_id,
    }
    resp.json.return_value = body
    resp.content = json.dumps(body).encode("utf-8")

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get("/api/v1/profiles/items/profile-id")

    assert r.status_code == 200
    assert r.headers["Content-Type"] == "application/json"

    data = r.json()
    for f in DENY_FIELDS:
        assert f not in data

    _assert_uuid(r.headers["X-Request-ID"])