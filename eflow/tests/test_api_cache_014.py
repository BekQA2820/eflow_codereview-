import datetime
import email.utils

MANIFEST_PATH = "/api/v1/manifest"


def test_if_modified_since_future_returns_200(mocker, api_client):
    now = datetime.datetime.now(datetime.timezone.utc)
    future = email.utils.format_datetime(now + datetime.timedelta(seconds=30))

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {
        "Content-Type": "application/json",
        "ETag": '"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"',
        "Cache-Control": "max-age=300",
        "Vary": "Authorization, X-Roles",
    }
    resp.json.return_value = {
        "widgets": [],
        "layout": {"rows": 1, "columns": 1, "gridType": "fixed"},
        "version": "1",
    }

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(
        MANIFEST_PATH,
        headers={"If-Modified-Since": future},
    )

    assert r.status_code == 200
    assert r.headers["ETag"]
