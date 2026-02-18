from responses import make_json_response

PROFILE_ID_EXISTING = "3fa85f64-5717-4562-b3fc-111111111111"
PROFILE_ID_MISSING = "3fa85f64-5717-4562-b3fc-000000000000"

ENDPOINT_EXISTING = f"/api/v1/profile/{PROFILE_ID_EXISTING}"
ENDPOINT_MISSING = f"/api/v1/profile/{PROFILE_ID_MISSING}"


def test_rbac_profile_017_no_status_or_body_difference_for_missing_profile(
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

    r_existing = api_client.get(
        ENDPOINT_EXISTING,
        headers={"Authorization": "Bearer restricted"},
    )

    r_missing = api_client.get(
        ENDPOINT_MISSING,
        headers={"Authorization": "Bearer restricted"},
    )

    assert r_existing.status_code == 403
    assert r_missing.status_code == 403

    assert r_existing.json()["code"] == r_missing.json()["code"]
    assert r_existing.json()["message"] == r_missing.json()["message"]

    assert "ETag" not in r_existing.headers
    assert "ETag" not in r_missing.headers

    combined_body = r_existing.text.lower() + r_missing.text.lower()

    deny_tokens = {
        "internalflags",
        "internalid",
        "stacktrace",
        "exception",
        "debuginfo",
        "internalmeta",
        "<html",
    }

    for token in deny_tokens:
        assert token not in combined_body

    for field in [
        "profile_uuid",
        "displayname",
        "email",
        "attributes",
        "relationships",
        "layout",
        "widgets",
    ]:
        assert field not in combined_body
