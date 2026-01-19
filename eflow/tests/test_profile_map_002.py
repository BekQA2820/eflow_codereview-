import json
import uuid
import re

UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")
DENY_FIELDS = {"internalId", "debugInfo", "stackTrace", "internalMeta"}


def test_profile_map_missing_internal_fields_not_exposed(mocker, api_client):
    """
    PROFILE MAP 002
    Отсутствие внутренних полей при маппинге профиля
    """

    trace_id = str(uuid.uuid4())

    body = {
        "id": "profile-200",
        "displayName": "Alexey Smirnov",
        "email": "alexey@test.ru",
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

    r = api_client.get("/api/v1/profiles/items/profile-200")

    assert r.status_code == 200
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"
    assert UUID_RE.match(r.headers["X-Request-ID"])

    data = r.json()
    assert set(data.keys()) == {"id", "displayName", "email", "traceId"}
    assert data["traceId"] == r.headers["X-Request-ID"]

    for f in DENY_FIELDS:
        assert f not in data