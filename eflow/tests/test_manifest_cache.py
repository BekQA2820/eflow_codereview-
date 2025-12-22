MANIFEST_PATH = "/api/v1/manifest"

def test_manifest_cache_miss_and_hit(api_client, auth_header):
    # первый request -  MISS
    r1 = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r1.status_code == 200
    assert r1.headers.get("Content-Type", "").startswith("application/json")
    assert r1.headers.get("Cache-Control") is not None
    assert r1.headers.get("X-Cache") in ("MISS", "MISS") or "MISS" in (r1.headers.get("X-Cache",""))
    # trace header present
    assert r1.headers.get("X-Request-ID") or r1.json().get("traceId")

    # Вттрой -  HIT
    r2 = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r2.status_code == 200
    assert r2.headers.get("X-Cache") in ("HIT", "HIT") or "HIT" in (r2.headers.get("X-Cache",""))
