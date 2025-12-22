import pytest

MANIFEST_PATH = "/api/v1/manifest"


class DummyResponse:
    def __init__(self, status_code=200, headers=None, json_data=None):
        self.status_code = status_code
        self.headers = headers or {}
        self._json = json_data

    def json(self):
        return self._json


def test_registry_rebuild_after_ttl_expiry(api_client, auth_header, mocker):

    v1 = {
        "version": "1",
        "widgets": [{"id": "w1"}],
        "layout": {"rows": 1, "columns": 1, "gridType": "fixed"}
    }

    v2 = {
        "version": "2",
        "widgets": [{"id": "w2"}],
        "layout": {"rows": 1, "columns": 1, "gridType": "fixed"}
    }

    r1 = DummyResponse(200, {"X-Cache": "MISS", "Content-Type": "application/json"}, v1)
    r2 = DummyResponse(200, {"X-Cache": "MISS", "Content-Type": "application/json"}, v2)

    mocker.patch("requests.get", side_effect=[r1, r2])

    # ---------- R1 ----------
    resp1 = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert resp1.status_code == 200
    body1 = resp1.json()

    # ---------- R2: TTL истёк ----------
    resp2 = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert resp2.status_code == 200
    body2 = resp2.json()

    assert body1 != body2, "После истечения TTL registry должен обновиться"
    assert body2["version"] != body1["version"], "version должен измениться"
