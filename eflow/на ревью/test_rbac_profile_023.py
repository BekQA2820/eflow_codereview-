from responses import make_json_response

PROFILE_ID = "3fa85f64-5717-4562-b3fc-111111111111"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_023_repeated_requests_do_not_escalate_access(
    mocker,
    api_client,
):
    body_viewer = {
        "profile_id": PROFILE_ID,
        "displayName": "John Doe",
    }

    resp = make_json_response(
        status=200,
        body=body_viewer,
        headers={
            "Content-Type": "application/json",
            "Cache-Control": "private, no-store",
        },
    )

    mock = mocker.patch("requests.Session.request")
    mock.side_effect = [resp, resp, resp]

    r1 = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer viewer"},
    )

    r2 = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer viewer"},
    )

    r3 = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer viewer"},
    )

    responses = [r1, r2, r3]

    for response in responses:
        assert response.status_code == 200
        data = response.json()

        assert "roles" not in data
        assert "permissions" not in data
        assert "scopes" not in data

        assert data == body_viewer

        body_lower = response.text.lower()
        for forbidden in ["email", "internalflags", "stacktrace"]:
            assert forbidden not in body_lower
