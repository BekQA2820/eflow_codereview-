import json
import uuid
import re

UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")


def test_profile_cache_vary_authorization(mocker, api_client):
    """
    PROFILE CACHE 067
    Ответ профиля должен различаться по Authorization (Vary)
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

    r = api_client.get(
        "/api/v1/profiles/items/profile-1",
        headers={"Authorization": "Bearer token-user"},
    )

    assert r.status_code == 200
    assert r.headers["Vary"] == "Authorization"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Content-Type"] == "application/json"
    assert UUID_RE.match(r.headers["X-Request-ID"])
    assert r.json()["traceId"] == r.headers["X-Request-ID"]