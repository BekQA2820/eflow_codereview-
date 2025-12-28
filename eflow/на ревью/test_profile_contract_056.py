import json
import uuid

DENY_FIELDS = {"debugInfo", "stackTrace", "internalMeta"}


def test_profile_contract_error_response_schema(mocker, api_client):
    """
    PROFILE CONTRACT 056
    Контракт ErrorResponse соответствует строгой схеме
    """

    trace_id = str(uuid.uuid4())

    error_body = {
        "code": "PROFILE_NOT_FOUND",
        "message": "Profile does not exist",
        "details": [],
        "traceId": trace_id,
    }

    resp = mocker.Mock()
    resp.status_code = 404
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "X-Request-ID": trace_id,
    }
    resp.json.return_value = error_body
    resp.content = json.dumps(error_body).encode("utf-8")

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get("/api/v1/profiles/items/missing-profile")

    assert r.status_code == 404
    assert r.headers["Content-Type"] == "application/json"

    data = r.json()
    assert set(data.keys()) == {"code", "message", "details", "traceId"}
    assert data["traceId"] == r.headers["X-Request-ID"]
    assert data["details"] == []

    for f in DENY_FIELDS:
        assert f not in data