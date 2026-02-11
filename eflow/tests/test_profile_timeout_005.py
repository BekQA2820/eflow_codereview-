import pytest
import concurrent.futures
import time

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH = f"/api/v1/employee-profiles/{PROFILE_ID}"
MAX_LATENCY_SECONDS = 2.0
CONCURRENT_USERS = 15

DENY_FIELDS = {
    "internalflags", "stacktrace", "exception", "<html",
    "sql", "debug", "backendonly"
}


@pytest.mark.integration
def test_profile_timeout_005_high_concurrency_load(api_client, auth_header):
    def timed_request():
        start_time = time.perf_counter()
        response = api_client.get(PATH, headers=auth_header)
        end_time = time.perf_counter()
        return response, end_time - start_time

    # Запуск конкурентной нагрузки
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_USERS) as executor:
        futures = [executor.submit(timed_request) for _ in range(CONCURRENT_USERS)]
        results = [f.result() for f in futures]

    for response, latency in results:
        # Проверка отсутствия "зависаний" по времени
        assert latency < MAX_LATENCY_SECONDS, f"Request took too long: {latency}s"

        # Если сервер не выдержал нагрузку, он должен вернуть 200 или ErrorResponse
        # Но не "пустой" 500 или HTML
        if response.status_code == 200:
            data = response.json()
            assert "id" in data
        else:
            # Если пошла деградация (например, 429 или 503), проверяем контракт
            assert response.status_code in [429, 503, 504]
            data = response.json()
            assert "code" in data
            assert "traceId" in data

        # Security Audit
        raw_low = response.text.lower()
        for field in DENY_FIELDS:
            assert field not in raw_low

        assert "prid" not in raw_low
        assert "12345" not in raw_low

    # Убеждаемся, что все запросы завершились
    assert len(results) == CONCURRENT_USERS