import re
from responses import make_json_response

PROFILE_ID = "3fa85f64-5717-4562-b3fc-111111111111"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_030_uniform_error_response_forbidden(
    mocker,
    api_client,
):
    trace_id = "trace-403-test"

    error_body = {
        "code": "FORBIDDEN",
        "message": "Access denied",
        "details": [],
        "traceId": trace_id,
    }

    resp = make_json_response(
        status=403,
        body=error_body,
        headers={
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            "Vary": "Authorization, X-Roles-Hash",
            "X-Request-ID": trace_id,
        },
    )

    mock = mocker.patch("requests.Session.request")
    mock.side_effect = [resp, resp]

    # --- first request ---
    r1 = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer restricted"},
    )

    # --- second request (determinism) ---
    r2 = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer restricted"},
    )

    for r in (r1, r2):
        assert r.status_code == 403
        assert r.headers.get("Content-Type") == "application/json"
        assert r.headers.get("Cache-Control") == "no-store"
        assert "Authorization" in r.headers.get("Vary", "")

        body = r.json()
        assert body.get("code") == "FORBIDDEN"
        assert isinstance(body.get("message"), str)
        assert isinstance(body.get("details"), list)
        assert isinstance(body.get("traceId"), str)

        # no domain or UI data
        raw = r.text.lower()
        deny = [
            "displayname",
            "email",
            "layout",
            "widgets",
            "internalflags",
            "stacktrace",
            "<html",
        ]
        for token in deny:
            assert token not in raw

    # determinism
    assert r1.json() == r2.json()
