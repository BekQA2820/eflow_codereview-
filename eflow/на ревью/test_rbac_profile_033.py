from responses import make_json_response

PROFILE_ID = "3fa85f64-5717-4562-b3fc-111111111111"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_033_forbidden_response_not_cached(
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

    resp1 = make_json_response(
        status=403,
        body=error_body_1,
        headers={
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            "Vary": "Authorization, X-Roles-Hash",
            "X-Request-ID": "trace-1",
        },
    )

    resp2 = make_json_response(
        status=403,
        body=error_body_2,
        headers={
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            "Vary": "Authorization, X-Roles-Hash",
            "X-Request-ID": "trace-2",
        },
    )

    mock = mocker.patch("requests.Session.request")
    mock.side_effect = [resp1, resp2]

    # first forbidden request
    r1 = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer restricted"},
    )

    # second forbidden request
    r2 = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer restricted"},
    )

    for r in (r1, r2):
        assert r.status_code == 403
        assert r.headers.get("Cache-Control") == "no-store"
        assert "ETag" not in r.headers
        assert "X-Cache" not in r.headers

        body = r.json()
        assert body.get("code") == "FORBIDDEN"

        raw = r.text.lower()
        deny = [
            "displayname",
            "email",
            "internalflags",
            "stacktrace",
            "<html",
        ]
        for token in deny:
            assert token not in raw

    # traceId may differ → no cache reuse
    assert r1.json()["traceId"] != r2.json()["traceId"]
