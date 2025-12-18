def test_invalid_jwt_signature(api_client):
    """
JWT с неверной подписью  401 Unauthorized.
Контракт: ErrorResponse(code, message, traceId).
    """

    bad_token = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkhBQ0tFRCBVU0VSIiwiaWF0IjoxNTE2MjM5MDIyfQ."
        "WRONG_SIGNATURE"
    )

    headers = {"Authorization": f"Bearer {bad_token}"}

    resp = api_client.get("/api/v1/manifest", headers=headers)

    assert resp.status_code == 401
    assert "code" in resp.json()
    assert "traceId" in resp.json()
    assert resp.json()["code"] in ("UNAUTHORIZED", "INVALID_TOKEN")
