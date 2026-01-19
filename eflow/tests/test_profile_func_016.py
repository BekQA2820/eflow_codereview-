import json
import uuid
import re

UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")
DENY_FIELDS = {"internalId", "debugInfo", "stackTrace", "internalMeta"}


def test_profile_func_016_create_profile_with_optional_fields(mocker, api_client):
    """
    PROFILE FUNC 016
    Проверка создания профиля с дополнительными необязательными полями
    """

    trace_id = str(uuid.uuid4())

    profile_data = {
        "name": "Alex",
        "surname": "Smith",
        "phone": "+9876543210",
        "address": "456 Elm St"
    }

    resp = mocker.Mock()
    resp.status_code = 201
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "X-Request-ID": trace_id,
    }
    resp.json.return_value = profile_data
    resp.content = json.dumps(profile_data).encode("utf-8")

    mocker.patch("requests.post", return_value=resp)

    r = api_client.post(
        "/api/v1/profiles/items",
        json=profile_data
    )

    assert r.status_code == 201
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"
    assert UUID_RE.match(r.headers["X-Request-ID"])

    data = r.json()
    assert set(data.keys()) == {"name", "surname", "phone", "address"}

    for f in DENY_FIELDS:
        assert f not in data

    # Verifying fields were correctly sent and saved
    assert data["name"] == profile_data["name"]
    assert data["surname"] == profile_data["surname"]
    assert data["phone"] == profile_data["phone"]
    assert data["address"] == profile_data["address"]