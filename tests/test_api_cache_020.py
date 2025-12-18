import re


MANIFEST_PATH = "/api/v1/manifest"


def test_etag_present_on_cache_hit(mocker, api_client):
    """
    API CACHE 020
    При HIT всегда возвращается strong ETag
    """

    etag = "b" * 32

    resp_miss = mocker.Mock()
    resp_miss.status_code = 200
    resp_miss.headers = {
        "Content-Type": "application/json",
        "ETag": etag,
        "Vary": "Authorization, X-Roles",
        "Cache-Control": "max-age=300",
        "X-Cache": "MISS",
    }
    resp_miss.json.return_value = {}
    resp_miss.content = b"{}"

    resp_hit = mocker.Mock()
    resp_hit.status_code = 200
    resp_hit.headers = {
        "Content-Type": "application/json",
        "ETag": etag,
        "Vary": "Authorization, X-Roles",
        "Cache-Control": "max-age=300",
        "X-Cache": "HIT",
    }
    resp_hit.json.return_value = {}
    resp_hit.content = b"{}"

    mocker.patch("requests.get", side_effect=[resp_miss, resp_hit])

    r1 = api_client.get(MANIFEST_PATH)
    r2 = api_client.get(MANIFEST_PATH)

    assert r2.headers["X-Cache"] == "HIT"
    assert "ETag" in r2.headers
    assert r1.headers["ETag"] == r2.headers["ETag"]
    assert re.fullmatch(r"[0-9a-f]{32}", r2.headers["ETag"])
