import datetime
import re

MANIFEST_PATH = "/api/v1/manifest"

ISO_8601_MS_UTC = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$"
)


def test_generated_at_iso8601_utc_with_ms(mocker, api_client):
    now = datetime.datetime.utcnow()

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/json"}
    resp.json.return_value = {
        "generatedAt": now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
        "widgets": [],
        "layout": {"rows": 0, "columns": 0, "gridType": "fixed"},
        "version": "1",
    }

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(MANIFEST_PATH)
    data = r.json()

    assert "generatedAt" in data
    ts = data["generatedAt"]
    assert isinstance(ts, str)
    assert ISO_8601_MS_UTC.match(ts)

    parsed = datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ")
    skew = abs((now - parsed).total_seconds())
    assert skew <= 5
