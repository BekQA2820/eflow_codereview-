import re


MANIFEST_PATH = "/api/v1/manifest"


def test_no_random_miss_on_fast_repeats(mocker, api_client):
    """
    API CACHE STRESS 001
    После первого MISS все быстрые повторы - HIT
    """

    etag = "c" * 32

    def make_resp(x_cache):
        r = mocker.Mock()
        r.status_code = 200
        r.headers = {
            "Content-Type": "application/json",
            "ETag": etag,
            "Vary": "Authorization, X-Roles",
            "Cache-Control": "max-age=300",
            "X-Cache": x_cache,
        }
        r.json.return_value = {}
        r.content = b"{}"
        return r

    responses = [make_resp("MISS")] + [make_resp("HIT") for _ in range(5)]
    mocker.patch("requests.get", side_effect=responses)

    results = []
    for _ in range(6):
        r = api_client.get(MANIFEST_PATH)
        results.append(r.headers["X-Cache"])
        assert re.fullmatch(r"[0-9a-f]{32}", r.headers["ETag"])

    assert results[0] == "MISS"
    assert all(x == "HIT" for x in results[1:])
