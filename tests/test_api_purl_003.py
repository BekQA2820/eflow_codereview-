import time

MANIFEST_PATH = "/api/v1/manifest"


def test_api_purl_retry_after_header(api_client, auth_header):
    """
    Выполнить много запросов - получить 429 - проверить Retry-After.
    """
    headers = auth_header.copy()

    # Делаем много запросов (70)
    for _ in range(70):
        r = api_client.get(MANIFEST_PATH, headers=headers)

        if r.status_code == 429:
            retry_after = r.headers.get("Retry-After")
            assert retry_after is not None
            assert retry_after.isdigit(), "Retry-After должен быть целым числом"
            assert int(retry_after) > 0

            time.sleep(int(retry_after) + 1)

            r2 = api_client.get(MANIFEST_PATH, headers=headers)
            assert r2.status_code != 429, "Rate-limit должен сбрасываться"
            return

    assert False, "429 не был получен — невозможно проверить Retry-After"
