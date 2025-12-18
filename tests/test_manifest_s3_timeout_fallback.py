import time

def test_manifest_s3_timeout_fallback(monkeypatch, api_client, auth_header):
    # simulate slow S3 response inside backend client
    def slow_s3(*args, **kwargs):
        time.sleep(5)
        raise TimeoutError("S3 timeout")

    monkeypatch.setattr("backend.s3_client.get_object", slow_s3)

    response = api_client.get("/api/v1/manifest", headers=auth_header)

    # must still return valid result (fallback from cache)
    assert response.status_code == 200
    assert "widgets" in response.json()
