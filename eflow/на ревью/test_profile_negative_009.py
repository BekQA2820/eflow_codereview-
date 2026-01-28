import json
import pytest
import requests
import uuid

PATH = "/api/v1/employee-profiles/3fa85f64-5717-4562-b3fc-2c963f66afa6"

DENY_FIELDS = {
    "signature", "mismatch", "crypto", "invalid_signature", "hs256",
    "rs256", "key", "algorithm", "stacktrace", "exception", "<html",
    "rbac", "permission", "forbidden"
}


@pytest.mark.integration
def test_profile_negative_009_invalid_signature_no_leak(mocker, api_client):
    invalid_sig_jwt = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.wrong_signature"

    def mock_security_interceptor(*args, **kwargs):
        trace_id = kwargs.get("headers", {}).get("X-Request-ID", str(uuid.uuid4()))
        error_body = {
            "code": "UNAUTHORIZED",
            "message": "Full authentication is required to access this resource",
            "details": [],
            "traceId": trace_id
        }
        js_error = json.dumps(error_body)

        resp = mocker.Mock(spec=requests.Response)
        resp.status_code = 401
        resp.json.return_value = error_body
        resp.text = js_error
        resp.content = js_error.encode("utf-8")
        resp.headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            "Vary": "Authorization",
            "X-Request-ID": trace_id
        }
        return resp

    mocker.patch.object(requests.Session, "request", side_effect=mock_security_interceptor)
    mocker.patch("requests.request", side_effect=mock_security_interceptor)

    for _ in range(2):
        unique_rid = str(uuid.uuid4())
        response = api_client.get(
            PATH,
            headers={
                "Authorization": invalid_sig_jwt,
                "X-Request-ID": unique_rid
            }
        )

        assert response.status_code == 401
        assert response.status_code != 403
        assert response.status_code != 500

        assert response.headers.get("Content-Type") == "application/json"
        assert "no-store" in response.headers.get("Cache-Control", "").lower()
        assert "Authorization" in response.headers.get("Vary", "")

        data = response.json()
        assert data["code"] == "UNAUTHORIZED"
        assert data["traceId"] == unique_rid

        raw_low = response.text.lower()
        for field in DENY_FIELDS:
            assert field not in raw_low
            assert field not in [str(k).lower() for k in data.keys()]

        assert "prid" not in raw_low
        assert "12345" not in raw_low
        # Убеждаемся, что в message нет намека на причину (mismatch)
        assert "signature" not in data["message"].lower()