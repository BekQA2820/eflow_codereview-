def test_manifest_content_type(api_client, auth_header):
    """
    Проверка Content Type строго application json.
    """
    resp = api_client.get("/api/v1/manifest", headers=auth_header)

    assert resp.status_code == 200
    assert resp.headers["Content-Type"].startswith("application/json")
