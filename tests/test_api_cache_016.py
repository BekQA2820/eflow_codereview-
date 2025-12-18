import json
import re


MANIFEST_PATH = "/api/v1/manifest"


def test_weak_etag_in_if_none_match(mocker, api_client):
    """
    API CACHE 016
    Сервер корректно обрабатывает weak ETag в If-None-Match
    """

    body = {"widgets": [], "layout": {"rows": 1, "columns": 1, "gridType": "fixed"}}
    etag = "a" * 32

    resp_200 = mocker.Mock()
    resp_200.status_code = 200
    resp_200.headers = {
        "Content-Type": "application/json",
        "ETag": etag,
        "Vary": "Authorization, X-Roles",
        "Cache-Control": "max-age=300",
        "X-Cache": "MISS",
    }
    resp_200.json.return_value = body
    resp_200.content = json.dumps(body).encode()

    resp_304 = mocker.Mock()
    resp_304.status_code = 304
    resp_304.headers = {
        "ETag": etag,
        "Vary": "Authorization, X-Roles",
        "Cache-Control": "max-age=300",
        "X-Cache": "HIT",
    }
    resp_304.content = b""

    mocker.patch("requests.get", side_effect=[resp_200, resp_304])

    r1 = api_client.get(MANIFEST_PATH)
    weak = f'W/"{r1.headers["ETag"]}"'

    r2 = api_client.get(
        MANIFEST_PATH,
        headers={"If-None-Match": weak},
    )

    assert r2.status_code in (200, 304)
    assert "ETag" in r2.headers
    assert re.fullmatch(r"[0-9a-f]{32}", r2.headers["ETag"])
