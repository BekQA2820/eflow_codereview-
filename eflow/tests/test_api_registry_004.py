import pytest

MANIFEST_PATH = "/api/v1/manifest"


class DummyResponse:
    def __init__(self, status_code=200, headers=None, json_data=None):
        self.status_code = status_code
        self.headers = headers or {}
        self._json = json_data

    def json(self):
        return self._json


def test_registry_fallback_on_corrupted_s3_data(api_client, auth_header, mocker):

    valid = {
        "version": "1",
        "widgets": [{"id": "w1"}],
        "layout": {"rows": 1, "columns": 2, "gridType": "fixed"}
    }

    corrupted = None  # невозможно распарсить → backend должен fallback

    r_valid = DummyResponse(200, {"Content-Type": "application/json", "X-Cache": "MISS"}, valid)
    r_corrupted = DummyResponse(200, {"Content-Type": "application/json", "X-Cache": "HIT"}, valid)  # fallback

    mocker.patch("requests.get", side_effect=[r_valid, r_corrupted])

    # ---------- R1: валидный ----------
    r1 = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r1.status_code == 200
    assert r1.json() == valid

    # ---------- R2: corrupted YAML → fallback ----------
    r2 = api_client.get(MANIFEST_PATH, headers=auth_header)

    assert r2.status_code == 200
    assert r2.headers.get("X-Cache") == "HIT"

    assert r2.json() == valid, (
        "При corrupted YAML backend обязан использовать fallback registry"
    )
