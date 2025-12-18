import pytest

MANIFEST_PATH = "/api/v1/manifest"


class DummyResponse:
    def __init__(self, status_code=200, headers=None, json_data=None):
        self.status_code = status_code
        self.headers = headers or {}
        self._json = json_data

    def json(self):
        return self._json


def test_registry_recovery_after_s3_failure(api_client, auth_header, mocker):

    v1 = {
        "version": "1",
        "widgets": [{"id": "w1"}],
        "layout": {"rows": 2, "columns": 2, "gridType": "fixed"}
    }

    v2 = {
        "version": "2",
        "widgets": [{"id": "w2"}],
        "layout": {"rows": 2, "columns": 2, "gridType": "fixed"}
    }

    r_ok_v1 = DummyResponse(200, {"Content-Type": "application/json", "X-Cache": "MISS"}, v1)
    r_fail = DummyResponse(200, {"Content-Type": "application/json", "X-Cache": "HIT"}, v1)   # fallback
    r_ok_v2 = DummyResponse(200, {"Content-Type": "application/json", "X-Cache": "MISS"}, v2)

    mocker.patch("requests.get", side_effect=[r_ok_v1, r_fail, r_ok_v2])

    # ---------- R1: нормальный ----------
    r1 = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r1.status_code == 200
    assert r1.json() == v1

    # ---------- R2: S3 падение → fallback ----------
    r2 = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r2.status_code == 200
    assert r2.headers.get("X-Cache") == "HIT"
    assert r2.json() == v1, "fallback должен вернуть старый registry"

    # ---------- R3: S3 восстановлен → новая версия ----------
    r3 = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r3.status_code == 200
    assert r3.json() == v2, "после восстановления S3 должен вернуться новый registry"
