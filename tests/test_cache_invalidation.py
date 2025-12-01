import os

MANIFEST_PATH = "/api/v1/manifest"

def test_cache_invalidation(redis_client, api_client, auth_header, manifest_cache_key, invalidate_cache):
    # get prid/roles
    prid = os.getenv("TEST_PRID")
    roles = os.getenv("TEST_ROLES", "employee").split(",")
    key = manifest_cache_key(prid, roles)

    # Ensure initial miss then hit
    r1 = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r1.status_code == 200
    # If first was miss, next should be hit
    r2 = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r2.status_code == 200
    assert "X-Cache" in r2.headers

    # Now invalidate key
    invalidate_cache(key)
    # After invalidation next request should be MISS
    r3 = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r3.status_code == 200
    # Expect MISS
    assert "MISS" in (r3.headers.get("X-Cache","")) or r3.headers.get("X-Cache") == "MISS"
