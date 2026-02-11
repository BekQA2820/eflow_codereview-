import json
import pytest
import requests
import uuid
import concurrent.futures

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH = f"/api/v1/employee-profiles/{PROFILE_ID}"

DENY_FIELDS = {
    "race", "condition", "lock", "mutex", "sync", "thread",
    "internalflags", "stacktrace", "exception", "<html", "configsource"
}


@pytest.mark.integration
def test_profile_timeout_014_concurrent_degradation_atomicity(mocker, api_client, auth_header):
    # Симулируем 5 одновременных запросов
    request_count = 5
    trace_ids = [str(uuid.uuid4()) for _ in range(request_count)]

    # Имитируем ошибку таймаута, которая должна быть консистентной для всех
    error_body_template = {
        "code": "GATEWAY_TIMEOUT",
        "message": "The service is temporarily overloaded",
        "details": []
    }

    def mock_side_effect(method, url, **kwargs):
        # Извлекаем X-Request-ID из заголовков текущего вызова
        rid = kwargs.get("headers", {}).get("X-Request-ID", "unknown")

        # Создаем индивидуальный ответ для каждого потока
        resp_data = error_body_template.copy()
        resp_data["traceId"] = rid
        js_error = json.dumps(resp_data)

        m_resp = mocker.Mock(spec=requests.Response)
        m_resp.status_code = 504
        m_resp.json.return_value = resp_data
        m_resp.text = js_error
        m_resp.content = js_error.encode("utf-8")
        m_resp.headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            "X-Request-ID": rid,
            "Vary": "Authorization"
        }
        return m_resp

    # Применяем универсальный патч согласно вашим правилам
    mocker.patch.object(requests.Session, "request", side_effect=mock_side_effect)
    mocker.patch("requests.request", side_effect=mock_side_effect)

    def send_request(rid):
        return api_client.get(
            PATH,
            headers={**auth_header, "X-Request-ID": rid}
        )

    # Выполняем параллельные запросы
    with concurrent.futures.ThreadPoolExecutor(max_workers=request_count) as executor:
        results = list(executor.map(send_request, trace_ids))

    # 1. Проверка детерминированности и атомарности
    for i, response in enumerate(results):
        rid = trace_ids[i]

        assert response.status_code == 504, f"Request {rid} failed with inconsistent status"

        data = response.json()
        # Проверка уникальности traceId для каждого запроса (отсутствие смешивания контекстов)
        assert data["traceId"] == rid
        assert data["code"] == "GATEWAY_TIMEOUT"

        # 2. Security Audit: проверка на отсутствие признаков гонки и утечек
        raw_low = response.text.lower()
        for field in DENY_FIELDS:
            assert field not in raw_low

        # 3. Проверка заголовков управления кэшем (должны запрещать кэш для всех ошибок)
        assert "no-store" in response.headers.get("Cache-Control", "").lower()

        # Проверка отсутствия старых ID
        assert "prid" not in raw_low
        assert "12345" not in raw_low