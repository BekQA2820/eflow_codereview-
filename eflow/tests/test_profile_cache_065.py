import json
import uuid


def test_profile_response_cache_control_no_store(mocker, api_client):
    """
    PROFILE CACHE 065
    Профиль не должен кэшироваться
    """

    trace_id = str(uuid.uuid4())

    body = {
        "id": "profile-1",
        "email": "user@test.com",
        "traceId": trace_id,
    }

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "X-Request-ID": trace_id,
    }
    resp.json.return_value = body
    resp.content = json.dumps(body).encode("utf-8")

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get("/api/v1/profiles/items/profile-1")

    assert r.status_code == 200
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"
    assert r.headers["Content-Type"] == "application/json"
    assert r.json()["traceId"] == r.headers["X-Request-ID"]