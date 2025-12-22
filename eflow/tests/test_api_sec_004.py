import pytest
from unittest.mock import Mock

MANIFEST = "/api/v1/manifest"


def test_error_response_consistent_format(api_client, mocker):

    body = {
        "code": "UNAUTHORIZED",
        "message": "token expired",
        "details": [],
        "traceId": "abc123"
    }

    resp = Mock()
    resp.status_code = 401
    resp.headers = {"Content-Type": "application/json", "X-Request-ID": "req-1"}
    resp.json.return_value = body

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(MANIFEST)
    assert r.status_code == 401

    assert r.headers["Content-Type"].startswith("application/json")
    assert "X-Request-ID" in r.headers

    err = r.json()
    assert isinstance(err, dict)
    for field in ("code", "message", "details", "traceId"):
        assert field in err, f"Отсутствует {field}"

    assert isinstance(err["code"], str)
    assert isinstance(err["message"], str)
    assert isinstance(err["details"], list)
    assert isinstance(err["traceId"], str) and err["traceId"]
