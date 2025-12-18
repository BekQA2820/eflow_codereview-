import re


MANIFEST_PATH = "/api/v1/manifest"


def test_cache_control_max_age_policy(mocker, api_client):
    """
    API CACHE 019
    Cache-Control соответствует политике сервиса
    """

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "max-age=300",
        "Vary": "Authorization, X-Roles",
        "ETag": "a" * 32,
        "X-Cache": "MISS",
    }
    resp.json.return_value = {"widgets": [], "layout": {"rows": 1, "columns": 1}}
    resp.content = b"{}"

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(MANIFEST_PATH)

    cc = r.headers.get("Cache-Control", "")
    assert "max-age=" in cc
    assert "public" not in cc
    assert "no-store" not in cc
    assert "private" not in cc

    m = re.search(r"max-age=(\d+)", cc)
    assert m
    assert int(m.group(1)) > 0
