import json
import uuid
import re


def _assert_uuid(v: str):
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        v,
    )


def test_profile_proto_008_array_item_with_unknown_field_rejected(mocker, api_client):
    """
    PROFILE PROTO 008
    Неизвестные поля внутри элементов массива отклоняются
    """

    trace_id = str(uuid.uuid4())

    error_body = {
        "code": "FIELD_NOT_ALLOWED",
        "message": "Unknown field in request",
        "details": [
            {"field": "phones[0].internal", "code": "NOT_ALLOWED"}
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
        json={
            "displayName": "Ivan",
            "phones": [
                {"value": "+79990000000", "internal": True}
            ],
        },
    )

    assert r.status_code == 400
    assert r.headers["Content-Type"] == "application/json"

    body = r.json()
    assert body["code"] == "FIELD_NOT_ALLOWED"
    assert body["details"][0]["code"] == "NOT_ALLOWED"
    assert body["traceId"] == r.headers["X-Request-ID"]

    _assert_uuid(body["traceId"])