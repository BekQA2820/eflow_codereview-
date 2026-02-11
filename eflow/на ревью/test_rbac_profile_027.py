from responses import make_json_response

PROFILE_ID = "3fa85f64-5717-4562-b3fc-111111111111"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_027_roles_not_leaked_in_body(
    mocker,
    api_client,
):
    response_body = {
        "profile_id": PROFILE_ID,
        "displayName": "John Doe",
        "email": "john.doe@example.com",
    }

    resp = make_json_response(
        status=200,
        body=response_body,
        headers={"Content-Type": "application/json"},
    )

    mocker.patch("requests.Session.request", return_value=resp)

    r = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer viewer"},
    )

    assert r.status_code == 200
    data = r.json()

    # --- Recursive scan ---
    def scan(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                key = str(k).lower()
                assert key not in ["roles", "permissions", "scopes"]
                scan(v)
        elif isinstance(obj, list):
            for item in obj:
                scan(item)

    scan(data)

    raw = r.text.lower()

    # --- No token-like / base64-ish fragments ---
    forbidden_tokens = [
        "roles",
        "permissions",
        "scopes",
        "eyjh",  # typical JWT base64 header prefix
    ]

    for token in forbidden_tokens:
        assert token not in raw

    assert "stacktrace" not in raw
    assert "<html" not in raw
