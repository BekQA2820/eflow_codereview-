import json
import re
 
 
MANIFEST_PATH = "/api/v1/manifest"
 
 
def test_cache_rebuild_after_invalidate(mocker, api_client):
    """
    API CACHE 017
    Кэш пересобирается после invalidate без ожидания TTL
    """
 
    body_v1 = {"widgets": [{"id": "a"}], "layout": {"rows": 1, "columns": 1}}
    body_v2 = {"widgets": [{"id": "b"}], "layout": {"rows": 1, "columns": 1}}
 
    def make_resp(body, etag, x_cache):
        r = mocker.Mock()
        r.status_code = 200
        r.headers = {
            "Content-Type": "application/json",
            "ETag": etag,
            "Vary": "Authorization, X-Roles",
            "Cache-Control": "max-age=300",
            "X-Cache": x_cache,
        }
        r.json.return_value = body
        r.content = json.dumps(body).encode("utf-8")
        return r
 
    # 1 - первичный запрос (кэш MISS)
    r1 = make_resp(body_v1, "a" * 32, "MISS")
 
    # 2 - повторный запрос (кэш HIT)
    r2 = make_resp(body_v1, "a" * 32, "HIT")
 
    # 3 - после invalidate кэш пересобран (MISS + новый ETag)
    r3 = make_resp(body_v2, "b" * 32, "MISS")
 
    mocker.patch("requests.get", side_effect=[r1, r2, r3])
 
    resp1 = api_client.get(MANIFEST_PATH)
    resp2 = api_client.get(MANIFEST_PATH)
    resp3 = api_client.get(MANIFEST_PATH)
 
    # Проверка поведения кэша
    assert resp1.headers["X-Cache"] == "MISS"
    assert resp2.headers["X-Cache"] == "HIT"
    assert resp3.headers["X-Cache"] == "MISS"
 
    # Проверка пересборки данных
    assert resp1.json() != resp3.json()
 
    # Проверка смены ETag
    assert resp1.headers["ETag"] != resp3.headers["ETag"]
    assert re.fullmatch(r"[0-9a-f]{32}", resp3.headers["ETag"])