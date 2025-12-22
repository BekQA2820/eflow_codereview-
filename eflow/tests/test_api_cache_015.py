import re
import pytest

MANIFEST_PATH = "/api/v1/manifest"

ETAG_RE = re.compile(r'^"[0-9a-f]{32}"$')


def test_etag_is_strong(mocker, api_client):
    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {
        "Content-Type": "application/json",
        "ETag": '"0123456789abcdef0123456789abcdef"',
    }
    resp.json.return_value = {
        "widgets": [],
        "layout": {"rows": 1, "columns": 1, "gridType": "fixed"},
        "version": "1",
    }

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(MANIFEST_PATH)

    etag = r.headers.get("ETag")
    assert etag is not None
    assert not etag.startswith("W/")
    assert ETAG_RE.match(etag)
