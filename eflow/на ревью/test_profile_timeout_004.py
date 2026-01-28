import pytest
import concurrent.futures

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH = f"/api/v1/employee-profiles/{PROFILE_ID}"

DENY_FIELDS = {
    "internalflags", "internalid", "backendonly", "stacktrace",
    "exception", "requiredroles", "configsource"
}


@pytest.mark.integration
def test_profile_timeout_004_parallel_read_consistency(api_client, auth_header):
    # Количество параллельных запросов
    num_requests = 3

    def make_request():
        # Важно: каждый поток выполняет независимый запрос через api_client
        return api_client.get(PATH, headers=auth_header)

    # 1. Запуск параллельных запросов
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_requests) as executor:
        futures = [executor.submit(make_request) for _ in range(num_requests)]
        responses = [f.result() for f in futures]

    # 2. Проверка консистентности ответов
    etags = []
    request_ids = set()
    payloads = []

    for resp in responses:
        assert resp.status_code == 200

        data = resp.json()
        payloads.append(data)

        # Сбор данных для сравнения
        if "ETag" in resp.headers:
            etags.append(resp.headers["ETag"])

        rid = resp.headers.get("X-Request-ID")
        assert rid is not None
        request_ids.add(rid)

        # Security Audit для каждого ответа
        raw_low = resp.text.lower()
        for field in DENY_FIELDS:
            assert field not in raw_low

    # 3. Анализ результатов гонки
    # Все X-Request-ID должны быть уникальными
    assert len(request_ids) == num_requests

    # Данные профиля (например, версия или содержимое) должны быть идентичны
    base_data = payloads[0]
    for p in payloads[1:]:
        assert p["id"] == base_data["id"]
        assert p["version"] == base_data["version"]

    # ETag должен быть одинаковым, если данные не менялись между запросами
    if etags:
        assert len(set(etags)) == 1

    # Проверка отсутствия старых ID
    assert "prid" not in responses[0].text.lower()