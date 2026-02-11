from responses import make_json_response

PROFILE_ID = "3fa85f64-5717-4562-b3fc-111111111111"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_038_no_partial_sensitive_data_leak(
    mocker,
    api_client,
):
    viewer_body = {
        "profile_id": PROFILE_ID,
        "displayName": "User",
    }

    resp = make_json_response(
        status=200,
        body=viewer_body,
        headers={
            "Content-Type": "application/json",
            "ETag": '"etag-viewer"',
            "X-Roles-Hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "Vary": "Authorization, X-Roles-Hash",
        },
    )

    mocker.patch("requests.Session.request", return_value=resp)

    r = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer viewer"},
    )

    assert r.status_code == 200

    data = r.json()

    # запрещенные поля полностью отсутствуют
    forbidden_fields = {
        "email",
        "phone",
        "salary",
        "roles",
        "permissions",
        "scopes",
    }

    for field in forbidden_fields:
        assert field not in data

    # отсутствие частичных значений
    raw = r.text.lower()
    partial_tokens = ["***", "null", "{}", '""']
    for token in partial_tokens:
        assert token not in raw

    # deny-list
    deny = [
        "internalflags",
        "internalid",
        "stacktrace",
        "exception",
        "debuginfo",
        "internalmeta",
        "<html",
    ]

    for token in deny:
        assert token not in raw
