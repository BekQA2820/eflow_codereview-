from responses import make_json_response

PROFILE_ID = "3fa85f64-5717-4562-b3fc-111111111111"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_021_no_privilege_escalation_on_combined_roles(
    mocker,
    api_client,
):
    body_viewer = {
        "profile_id": PROFILE_ID,
        "displayName": "John Doe",
    }

    body_combined = {
        "profile_id": PROFILE_ID,
        "displayName": "John Doe",
    }

    resp_viewer = make_json_response(
        status=200,
        body=body_viewer,
        headers={"Content-Type": "application/json"},
    )

    resp_combined = make_json_response(
        status=200,
        body=body_combined,
        headers={"Content-Type": "application/json"},
    )

    mock = mocker.patch("requests.Session.request")
    mock.side_effect = [resp_viewer, resp_combined]

    r_viewer = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer viewer"},
    )

    r_combined = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer viewer+employee_basic"},
    )

    assert r_viewer.status_code == 200
    assert r_combined.status_code == 200

    fields_viewer = set(r_viewer.json().keys())
    fields_combined = set(r_combined.json().keys())

    assert fields_combined == fields_viewer

    for forbidden in ["roles", "permissions", "scopes"]:
        assert forbidden not in r_viewer.json()
        assert forbidden not in r_combined.json()
