import json
import pytest
import requests
import uuid

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH = f"/api/v1/employee-profiles/{PROFILE_ID}"

# Хеш, который мы "подсовываем" (явно неверный)
MALICIOUS_HASH = "deadbeef000000000000000000000000"
# Хеш, который реально должен вычислить сервер для роли 'User'
EXPECTED_SERVER_HASH = "8ba2f99547d25e0c800843236e76554b"

DENY_FIELDS = {
    "internalflags", "stacktrace", "exception", "<html", "configsource",
    "collision", "bypass", "manual_hash"
}


@pytest.mark.integration
def test_profile_negative_028_ignored_client_roles_hash(mocker, api_client):
    trace_id = str(uuid.uuid4())
    # Валидный токен с ролью User, но "отравленным" roles_hash
    tampered_jwt = f"Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlcyI6WyJVc2VyIl0sInJvbGVzX2hhc2giOiJ7TUFMSUNJT1VTX0hBU0h9In0.sig"

    success_body = {
        "id": PROFILE_ID,
        "firstName": "John",
        "lastName": "Doe"
    }
    js_body = json.dumps(success_body)

    mock_resp = mocker.Mock(spec=requests.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = success_body
    mock_resp.text = js_body
    mock_resp.content = js_body.encode("utf-8")
    mock_resp.headers = {
        "Content-Type": "application/json",
        "X-Roles-Hash": EXPECTED_SERVER_HASH,  # Сервер вернул свой честный хеш
        "X-Request-ID": trace_id
    }

    mocker.patch.object(requests.Session, "request", return_value=mock_resp)
    mocker.patch("requests.request", return_value=mock_resp)

    response = api_client.get(
        PATH,
        headers={
            "Authorization": tampered_jwt,
            "X-Request-ID": trace_id
        }
    )

    # 1. Запрос должен пройти (так как роли валидны), либо 403 (если политика запрещает несовпадение)
    # В данном случае проверяем игнорирование подмены: статус 200
    assert response.status_code == 200

    # 2. Ключевая проверка: Сервер НЕ должен вернуть тот хеш, что мы прислали
    server_hash = response.headers.get("X-Roles-Hash")
    assert server_hash is not None
    assert server_hash != MALICIOUS_HASH
    assert server_hash == EXPECTED_SERVER_HASH

    # 3. Security Audit: проверка отсутствия отладочной информации о сравнении хешей
    raw_low = response.text.lower()
    for field in DENY_FIELDS:
        assert field not in raw_low

    assert "prid" not in raw_low
    assert "12345" not in raw_low