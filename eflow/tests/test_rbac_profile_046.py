from responses import make_json_response

PROFILE_ID = "3fa85f64-5717-4562-b3fc-111111111111"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_046_uniform_forbidden_contract(
    mocker,
    api_client,
):
    error_body_1 = {
        "code": "FORBIDDEN",
        "message": "Access denied",
        "details": [],
        "traceId": "trace-1",
    }

    error_body_2 = {
        "code": "FORBIDDEN",
        "message": "Access denied",
        "details": [],
        "traceId": "trace-2",
    }

    error_body_3 = {
        "code": "FORBIDDEN",
        "message": "Access denied",
        "details": [],
        "traceId": "trace-3",
    }

    resp1 = make_json_response(
        status=403,
        body=error_body_1,
        headers={
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            "Vary": "Authorization, X-Roles-Hash",
        },
    )

    resp2 = make_json_response(
        status=403,
        body=error_body_2,
        headers={
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            "Vary": "Authorization, X-Roles-Hash",
        },
    )

    resp3 = make_json_response(
        status=403,
        body=error_body_3,
        headers={
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            "Vary": "Authorization, X-Roles-Hash",
        },
    )

    mock = mocker.patch("requests.Session.request")
    mock.side_effect = [resp1, resp2, resp3]

    r1 = api_client.get(ENDPOINT, headers={"Authorization": "Bearer restricted"})
    r2 = api_client.get(ENDPOINT, headers={"Authorization": "Bearer empty"})
    r3 = api_client.get(ENDPOINT, headers={"Authorization": "Bearer unknown"})

    for r in (r1, r2, r3):
        assert r.status_code == 403
        body = r.json()
        assert body["code"] == "FORBIDDEN"
        assert body["message"] == "Access denied"
        assert isinstance(body["details"], list)
        assert "traceId" in body

        raw = r.text.lower()
        for forbidden in [
            "profile_id",
            "displayname",
            "email",
            "internalflags",
            "stacktrace",
            "exception",
            "<html",
        ]:
            assert forbidden not in raw
