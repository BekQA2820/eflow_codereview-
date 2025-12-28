import json
import uuid
import re


def _assert_uuid(v: str):
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        v,
    )


def test_profile_obs_008_unique_trace_per_request(mocker, api_client):
    """
    PROFILE OBS 008
    Каждый ответ обязан иметь уникальный X-Request-ID
    """

    trace_1 = str(uuid.uuid4())
    trace_2 = str(uuid.uuid4())

    body = {"profile_uuid": "profile-id"}

    r1 = mocker.Mock()
    r1.status_code = 200
    r1.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "private, no-store",
        "Vary": "Authorization",
        "X-Request-ID": trace_1,
    }
    r1.json.return_value = body
    r1.content = json.dumps(body).encode("utf-8")

    r2 = mocker.Mock()
    r2.status_code = 200
    r2.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "private, no-store",
        "Vary": "Authorization",
        "X-Request-ID": trace_2,
    }
    r2.json.return_value = body
    r2.content = json.dumps(body).encode("utf-8")

    mocker.patch("requests.get", side_effect=[r1, r2])

    g1 = api_client.get("/api/v1/profiles/items/profile-id")
    g2 = api_client.get("/api/v1/profiles/items/profile-id")

    assert g1.headers["X-Request-ID"] != g2.headers["X-Request-ID"]

    _assert_uuid(g1.headers["X-Request-ID"])
    _assert_uuid(g2.headers["X-Request-ID"])