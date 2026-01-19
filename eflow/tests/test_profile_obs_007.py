import json
import uuid
import re


def _assert_uuid(v: str):
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        v,
    )


def test_profile_obs_007_trace_propagation(mocker, api_client):
    """
    PROFILE OBS 007
    traceId должен строго совпадать с X-Request-ID
    """

    trace_id = str(uuid.uuid4())

    body = {
        "profile_uuid": "profile-id",
        "displayName": "Ivan",
        "traceId": trace_id,
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
    assert data["traceId"] == r.headers["X-Request-ID"]

    _assert_uuid(data["traceId"])