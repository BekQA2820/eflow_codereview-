import uuid
from responses import make_json_response

PROFILE_ID = "3fa85f64-5717-4562-b3fc-111111111111"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_022_forbidden_even_if_profile_is_self(
    mocker,
    api_client,
):
    trace_id = str(uuid.uuid4())

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

    r1 = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer restricted"},
    )

    r2 = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer restricted"},
    )

    for response in (r1, r2):
        assert response.status_code == 403

        data = response.json()
        assert data.get("code") == "FORBIDDEN"
        assert isinstance(data.get("message"), str)
        assert data.get("traceId")
        assert isinstance(data.get("details"), list)

        assert response.headers.get("Cache-Control") == "no-store"
        assert response.headers.get("X-Request-ID") == data.get("traceId")

        body_lower = response.text.lower()
        for forbidden in [
            "profile_id",
            "displayname",
            "email",
            "layout",
            "widgets",
            "internalflags",
            "stacktrace",
            "<html",
        ]:
            assert forbidden not in body_lower
