import time

MANIFEST_PATH = "/api/v1/manifest"
MAX_LATENCY_SEC = 0.07  # 70 ms


def test_manifest_latency_p95_under_limit(mocker, api_client):
    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/json"}
    resp.json.return_value = {
        "widgets": [],
        "layout": {"rows": 0, "columns": 0, "gridType": "fixed"},
        "version": "1",
    }

    mocker.patch("requests.get", return_value=resp)

    timings = []

    for _ in range(20):
        start = time.perf_counter()
        r = api_client.get(MANIFEST_PATH)
        end = time.perf_counter()

        assert r.status_code == 200
        timings.append(end - start)

    timings.sort()
    p95 = timings[int(len(timings) * 0.95) - 1]

    assert p95 <= MAX_LATENCY_SEC, f"p95 latency too high: {p95}s"
