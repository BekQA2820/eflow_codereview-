import datetime
import email.utils
import pytest

MANIFEST_PATH = "/api/v1/manifest"


def test_last_modified_header_and_clock_skew(mocker, api_client):
    now = datetime.datetime.now(datetime.timezone.utc)
    last_modified = email.utils.format_datetime(now)

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {
        "Content-Type": "application/json",
        "Last-Modified": last_modified,
        "X-Request-ID": "lm-001",
    }
    resp.json.return_value = {
        "widgets": [],
        "layout": {"rows": 1, "columns": 1, "gridType": "fixed"},
        "version": "1",
    }

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(MANIFEST_PATH)

    assert r.status_code == 200
    assert "Last-Modified" in r.headers

    lm = email.utils.parsedate_to_datetime(r.headers["Last-Modified"])
    delta = abs((now - lm).total_seconds())

    assert delta <= 5
