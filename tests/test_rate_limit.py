MANIFEST_PATH = "/api/v1/manifest"

def test_rate_limit_per_user(api_client, token_valid):
    # дает 61 реквест
    headers = {"Authorization": f"Bearer {token_valid}"} if token_valid else {}
    last_resp = None
    for i in range(61):
        r = api_client.get(MANIFEST_PATH, headers=headers)
        last_resp = r
    # Expect last => 429
    assert last_resp is not None
    assert last_resp.status_code == 429
    # проверяет retry after
    ra = last_resp.headers.get("Retry-After")
    assert ra is not None
    assert ra.isdigit()
    # тут должен быть 0
    rem = last_resp.headers.get("X-RateLimit-Remaining")
    assert rem == "0" or rem == 0 or int(rem) == 0
