import json

MANIFEST_PATH = "/api/v1/manifest"


def test_observability_headers_and_trace_consistency(mocker, api_client):
    resp_miss = mocker.Mock()
    resp_miss.status_code = 200
    resp_miss.headers = {
        "Content-Type": "application/json",
        "X-Request-ID": "req-1",
        "X-Cache": "MISS",
        "X-Roles-Hash": "a" * 32,
    }
    resp_miss.json.return_value = {
        "widgets": [],
        "layout": {"rows": 0, "columns": 0, "gridType": "fixed"},
        "version": "1",
    }
    resp_miss.content = json.dumps(resp_miss.json.return_value).encode()

    resp_hit = mocker.Mock()
    resp_hit.status_code = 200
    resp_hit.headers = {
        "Content-Type": "application/json",
        "X-Request-ID": "req-2",
        "X-Cache": "HIT",
        "X-Roles-Hash": "a" * 32,
    }
    resp_hit.json.return_value = resp_miss.json.return_value
    resp_hit.content = resp_miss.content

    mocker.patch("requests.get", side_effect=[resp_miss, resp_hit])

    r1 = api_client.get(MANIFEST_PATH)
    r2 = api_client.get(MANIFEST_PATH)

    assert r1.headers["X-Cache"] == "MISS"
    assert r2.headers["X-Cache"] == "HIT"

    assert r1.headers["X-Request-ID"] != r2.headers["X-Request-ID"]
    assert r1.headers["X-Roles-Hash"] == r2.headers["X-Roles-Hash"]
