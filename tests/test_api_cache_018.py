import json
import re


MANIFEST_PATH = "/api/v1/manifest"


def test_cache_race_single_rebuild(mocker, api_client):
    """
    API CACHE 018
    Только один запрос делает rebuild, второй получает HIT
    """

    body = {"widgets": [{"id": "a"}], "layout": {"rows": 1, "columns": 1}}
    etag = "c" * 32

    r_rebuild = mocker.Mock()
    r_rebuild.status_code = 200
    r_rebuild.headers = {
        "Content-Type": "application/json",
        "ETag": etag,
        "Vary": "Authorization, X-Roles",
        "Cache-Control": "max-age=300",
        "X-Cache": "MISS",
    }
    r_rebuild.json.return_value = body
    r_rebuild.content = json.dumps(body).encode()

    r_hit = mocker.Mock()
    r_hit.status_code = 200
    r_hit.headers = {
        "Content-Type": "application/json",
        "ETag": etag,
        "Vary": "Authorization, X-Roles",
        "Cache-Control": "max-age=300",
        "X-Cache": "HIT",
    }
    r_hit.json.return_value = body
    r_hit.content = json.dumps(body).encode()

    mocker.patch("requests.get", side_effect=[r_rebuild, r_hit])

    r1 = api_client.get(MANIFEST_PATH)
    r2 = api_client.get(MANIFEST_PATH)

    assert r1.headers["X-Cache"] == "MISS"
    assert r2.headers["X-Cache"] in {"HIT", "WAIT+HIT"}

    assert r1.headers["ETag"] == r2.headers["ETag"]
    assert re.fullmatch(r"[0-9a-f]{32}", r1.headers["ETag"])
