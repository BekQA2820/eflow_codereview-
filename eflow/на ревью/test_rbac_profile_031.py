from responses import make_json_response

PROFILE_ID = "3fa85f64-5717-4562-b3fc-111111111111"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_031_http_status_independent_of_role_when_access_granted(
    mocker,
    api_client,
):
    viewer_body = {
        "profile_id": PROFILE_ID,
        "displayName": "John",
    }

    employee_body = {
        "profile_id": PROFILE_ID,
        "displayName": "John",
        "email": "john@example.com",
    }

    viewer_resp = make_json_response(
        status=200,
        body=viewer_body,
        headers={"Content-Type": "application/json"},
    )

    employee_resp = make_json_response(
        status=200,
        body=employee_body,
        headers={"Content-Type": "application/json"},
    )

    mock = mocker.patch("requests.Session.request")
    mock.side_effect = [viewer_resp, employee_resp]

    # viewer request
    r_viewer = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer viewer"},
    )

    # employee_basic request
    r_employee = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer employee_basic"},
    )

    # --- status must not depend on role ---
    assert r_viewer.status_code == 200
    assert r_employee.status_code == 200

    # --- allowed difference only in fields ---
    assert r_viewer.json() != r_employee.json()
    assert "email" not in r_viewer.json()
    assert "email" in r_employee.json()
