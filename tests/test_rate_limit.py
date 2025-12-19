MANIFEST_PATH = "/api/v1/manifest"


def test_rate_limit_per_user(mocker, api_client, token_valid):
    """
    API RATE LIMIT
    Проверка контракта ответа при превышении лимита
    """

    headers = {"Authorization": f"Bearer {token_valid}"} if token_valid else {}

    resp = mocker.Mock()
    resp.status_code = 429
    resp.headers = {
        "Content-Type": "application/json",
        "Retry-After": "1",
        "X-RateLimit-Remaining": "0",
        "X-Request-ID": "trace-rate-001",
    }
    resp.json.return_value = {
        "code": "RATE_LIMIT_EXCEEDED",
        "message": "Too many requests",
        "traceId": "trace-rate-001",
    }

    # ВАЖНО: мок именно requests.request
    mocker.patch("requests.request", return_value=resp)

    r = api_client.get(MANIFEST_PATH, headers=headers)

    assert r.status_code == 429

    ra = r.headers.get("Retry-After")
    assert ra is not None
    assert ra.isdigit()

    rem = r.headers.get("X-RateLimit-Remaining")
    assert rem is not None
    assert int(rem) == 0
