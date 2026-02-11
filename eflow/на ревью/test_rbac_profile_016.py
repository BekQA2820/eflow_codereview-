from responses import make_json_response

PROFILE_ID_EXISTING = "3fa85f64-5717-4562-b3fc-111111111111"
PROFILE_ID_MISSING = "3fa85f64-5717-4562-b3fc-000000000000"

ENDPOINT_EXISTING = f"/api/v1/profile/{PROFILE_ID_EXISTING}"
ENDPOINT_MISSING = f"/api/v1/profile/{PROFILE_ID_MISSING}"


def test_rbac_profile_016_uniform_forbidden_contract_no_existence_leak(
    mocker,
    api_client,
):
    error_body = {
        "code": "FORBIDDEN",
        "message": "access denied",
        "details": [],
        "traceId": "trace-forbidden",
    }

    resp_1 = make_json_response(
        status=403,
        body=error_body,
        headers={
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            "Vary": "Authorization, X-Roles-Hash",
        },
    )

    resp_2 = make_json_response(
        status=403,
        body=error_body,
        headers={
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            "Vary": "Authorization, X-Roles-Hash",
        },
    )

    mock = mocker.patch("requests.Session.request")
    mock.side_effect = [resp_1, resp_2]

    r1 = api_client.get(
        ENDPOINT_EXISTING,
        headers={
            "Authorization": "Bearer restricted",
            "Accept": "application/json",
        },
    )

    r2 = api_client.get(
        ENDPOINT_MISSING,
        headers={
            "Authorization": "Bearer restricted",
            "Accept": "application/json",
        },
    )

    assert r1.status_code == 403
    assert r2.status_code == 403

    assert r1.json()["code"] == "FORBIDDEN"
    assert r2.json()["code"] == "FORBIDDEN"

    assert r1.json()["message"] == r2.json()["message"]
    assert isinstance(r1.json()["details"], list)
    assert isinstance(r2.json()["traceId"], str)

    assert "ETag" not in r1.headers
    assert "ETag" not in r2.headers

    assert r1.headers["Cache-Control"] == "no-store"
    assert "Authorization" in r1.headers["Vary"]

    body_combined = r1.text.lower() + r2.text.lower()

    forbidden = [
        "profile_uuid",
        "displayname",
        "email",
        "layout",
        "widgets",
        "attributes",
        "relationships",
    ]

    for field in forbidden:
        assert field not in body_combined
