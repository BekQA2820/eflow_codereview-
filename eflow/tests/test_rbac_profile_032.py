import re
from responses import make_json_response

PROFILE_ID = "3fa85f64-5717-4562-b3fc-000000000000"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_032_authorized_user_gets_404_for_missing_profile(
    mocker,
    api_client,
):
    trace_id = "trace-404-test"

    error_body = {
        "code": "NOT_FOUND",
        "message": "Resource not found",
        "details": [],
        "traceId": trace_id,
    }

    resp = make_json_response(
        status=404,
        body=error_body,
        headers={
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            "Vary": "Authorization",
            "X-Request-ID": trace_id,
        },
    )

    mock = mocker.patch("requests.Session.request")
    mock.side_effect = [resp, resp]

    # first request
    r1 = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer viewer"},
    )

    # second request (determinism)
    r2 = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer viewer"},
    )

    for r in (r1, r2):
        assert r.status_code == 404
        assert r.headers.get("Content-Type") == "application/json"
        assert r.headers.get("Cache-Control") == "no-store"
        assert "Authorization" in r.headers.get("Vary", "")
        assert "ETag" not in r.headers
        assert "X-Request-ID" in r.headers

        body = r.json()
        assert body.get("code") == "NOT_FOUND"
        assert isinstance(body.get("message"), str)
        assert isinstance(body.get("details"), list)
        assert isinstance(body.get("traceId"), str)

        raw = r.text.lower()
        deny = [
            "displayname",
            "email",
            "internalflags",
            "internalid",
            "debuginfo",
            "stacktrace",
            "exception",
            "<html",
        ]
        for token in deny:
            assert token not in raw

    # ensure this is truly 404, not RBAC 403
    assert r1.status_code != 403
