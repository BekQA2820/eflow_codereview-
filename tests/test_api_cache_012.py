import json
import pytest

MANIFEST_PATH = "/api/v1/manifest"

REQUIRED_VARY = "Authorization, X-Roles"


def make_response(mocker, *, status=200, body=None, vary=REQUIRED_VARY):
    r = mocker.Mock()
    r.status_code = status
    r.headers = {
        "Content-Type": "application/json",
        "Vary": vary,
        "ETag": "c" * 32,
        "Cache-Control": "private, max-age=300",
        "X-Cache": "MISS",
        "X-Request-ID": "req-id",
    }
    r.json.return_value = body or {"layout": {}, "widgets": []}
    r.text = json.dumps(r.json.return_value)
    return r


def test_manifest_vary_present_without_authorization(mocker, api_client):
    """
    API CACHE 012
    Ответ без Authorization все равно обязан содержать Vary
    """

    r = make_response(mocker)
    mocker.patch("requests.get", return_value=r)

    resp = api_client.get(MANIFEST_PATH)

    assert resp.status_code == 200
    assert resp.headers.get("Vary") == REQUIRED_VARY
    assert resp.headers.get("ETag")
    assert resp.headers.get("Cache-Control")

    raw = resp.text.lower()
    assert "<html" not in raw
    assert "stacktrace" not in raw


def test_manifest_vary_same_for_different_tokens(mocker, api_client):
    """
    API CACHE 012
    Vary одинаков для разных пользователей и токенов
    """

    r1 = make_response(mocker)
    r2 = make_response(mocker)

    mocker.patch("requests.get", side_effect=[r1, r2])

    resp1 = api_client.get(MANIFEST_PATH, headers={"Authorization": "Bearer tokenA"})
    resp2 = api_client.get(MANIFEST_PATH, headers={"Authorization": "Bearer tokenB"})

    assert resp1.headers.get("Vary") == REQUIRED_VARY
    assert resp2.headers.get("Vary") == REQUIRED_VARY
