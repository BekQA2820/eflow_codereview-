from responses import make_json_response

PROFILE_ID = "3fa85f64-5717-4562-b3fc-111111111111"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_035_empty_roles_forbidden(
    mocker,
    api_client,
):
    error_body_1 = {
        "code": "FORBIDDEN",
        "message": "Access denied",
        "details": [],
        "traceId": "trace-empty-1",
    }

    error_body_2 = {
        "code": "FORBIDDEN",
        "message": "Access denied",
        "details": [],
        "traceId": "trace-empty-2",
    }

    resp1 = make_json_response(
        status=403,
        body=error_body_1,
        headers={
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            "Vary": "Authorization",
            "X-Request-ID": "trace-empty-1",
        },
    )

    resp2 = make_json_response(
        status=403,
        body=error_body_2,
        headers={
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            "Vary": "Authorization",
            "X-Request-ID": "trace-empty-2",
        },
    )

    mock = mocker.patch("requests.Session.request")
    mock.side_effect = [resp1, resp2]

    r1 = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer empty-roles"},
    )

    r2 = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer empty-roles"},
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

    # determinism of contract (traceId may differ)
    assert r1.status_code == r2.status_code == 403
