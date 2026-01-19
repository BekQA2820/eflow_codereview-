import json
import uuid
import re

UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")


def test_profile_field_mapping_internal_to_public(mocker, api_client):
    """
    PROFILE MAP 001
    Корректное отображение внутренних полей в публичную модель
    """

    trace_id = str(uuid.uuid4())

    body = {
        "id": "profile-77",
        "displayName": "Petr Sidorov",
        "phone": "+79991112233",
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

    r = api_client.get("/api/v1/profiles/items/profile-77")

    assert r.status_code == 200
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"
    assert UUID_RE.match(r.headers["X-Request-ID"])

    data = r.json()
    assert data["displayName"] == "Petr Sidorov"
    assert data["phone"] == "+79991112233"
    assert data["traceId"] == r.headers["X-Request-ID"]

    assert "internal_name" not in data
    assert "internal_phone" not in data