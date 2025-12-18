import threading


def test_rate_limit_parallel_requests(mocker, api_client):
    limit = 60
    state = {"count": 0}

    def fake_get(url, headers=None, **kwargs):
        resp = mocker.Mock()
        state["count"] += 1

        if state["count"] > limit:
            resp.status_code = 429
            resp.headers = {"Retry-After": "1"}
            resp.json.return_value = {"code": "RATE_LIMIT_EXCEEDED"}
        else:
            resp.status_code = 200
            resp.headers = {"X-RateLimit-Remaining": str(limit - state["count"])}
            resp.json.return_value = {"ok": True}

        return resp

    mocker.patch("requests.get", side_effect=fake_get)

    results = []

    def make_call():
        r = api_client.get(
            "/api/v1/manifest",
            headers={"Authorization": "Bearer token-parallel"},
        )
        results.append(r.status_code)

    threads = [threading.Thread(target=make_call) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert 429 not in results
    assert all(code == 200 for code in results)
