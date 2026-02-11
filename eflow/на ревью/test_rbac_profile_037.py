from responses import make_json_response

PROFILE_ID = "3fa85f64-5717-4562-b3fc-111111111111"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_037_null_or_missing_roles_forbidden(
    mocker,
    api_client,
):
    error_body_1 = {
        "code": "FORBIDDEN",
        "message": "Access denied",
        "details": [],
        "traceId": "trace-null-1",
    }

    error_body_2 = {
        "code": "FORBIDDEN",
        "message": "Access denied",
        "details": [],
        "traceId": "trace-null-2",
    }

    resp1 = make_json_response(
        status=403,
        body=error_body_1,
        headers={
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            "Vary": "Authorization",
            "X-Request-ID": "trace-null-1",
        },
    )

    resp2 = make_json_response(
        status=403,
        body=error_body_2,
        headers={
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            "Vary": "Authorization",
            "X-Request-ID": "trace-null-2",
        },
    )

    mock = mocker.patch("requests.Session.request")
    mock.side_effect = [resp1, resp2]

    r1 = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer null-roles"},
    )

    r2 = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer null-roles"},
    )

    for r in (r1, r2):
        assert r.status_code == 403
        assert r.headers.get("Cache-Control") == "no-store"
        assert "Authorization" in r.headers.get("Vary", "")

        body = r.json()
        assert body.get("code") == "FORBIDDEN"
        assert isinstance(body.get("traceId"), str)

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

    assert r1.status_code == r2.status_code == 403
