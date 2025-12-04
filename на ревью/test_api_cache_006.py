
from email.utils import parsedate_to_datetime, format_datetime

MANIFEST_PATH = "/api/v1/manifest"


def test_api_cache_last_modified(api_client, auth_header):
    r1 = api_client.get(MANIFEST_PATH, headers=auth_header)
    assert r1.status_code == 200

    lm = r1.headers.get("Last-Modified")
    assert lm, "Ожидается заголовок Last-Modified"

    dt = parsedate_to_datetime(lm)

    headers = auth_header.copy()
    headers["If-Modified-Since"] = format_datetime(dt)

    r2 = api_client.get(MANIFEST_PATH, headers=headers)
    assert r2.status_code in (200, 304)
