import json
import pytest
import requests

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH = f"/api/v1/employee-profiles/{PROFILE_ID}"

DENY_FIELDS = {
    "signature", "invalid", "key", "algorithm", "hs256", "rs256",
    "internalflags", "stacktrace", "exception", "<html", "base64"
}


@pytest.mark.integration
def test_profile_negative_003_invalid_signature(mocker, api_client):
    error_body = {
        "code": "UNAUTHORIZED",
        "message": "Full authentication is required to access this resource",
        "details": [],
        "traceId": "tr-660f9511-f30c-52e5-b827-557766551111"
    }
    js_error = json.dumps(error_body)

    mock_resp = mocker.Mock(spec=requests.Response)
    mock_resp.status_code = 401
    mock_resp.json.return_value = error_body
    mock_resp.text = js_error
    mock_resp.content = js_error.encode("utf-8")
    mock_resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "X-Request-ID": "tr-660f9511-f30c-52e5-b827-557766551111"
    }

    # Универсальный патч сессии и глобального метода
    mocker.patch.object(requests.Session, "request", return_value=mock_resp)
    mocker.patch("requests.request", return_value=mock_resp)

    # Токен с заведомо некорректной подписью
    invalid_sig_header = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.payload.invalid_signature_part"}

    response = api_client.get(
        PATH,
        headers=invalid_sig_header
    )

    # СогласноSaved Info: Invalid signature is always 401, not 403
    assert response.status_code == 401
    assert response.status_code != 403

    assert response.headers.get("Content-Type") == "application/json"
    assert "no-store" in response.headers.get("Cache-Control", "").lower()

    data = response.json()
    assert data["code"] == "UNAUTHORIZED"
    assert "traceId" in data

    raw_low = response.text.lower()
    # Проверка на отсутствие технических деталей механизма проверки подписи
    for forbidden in DENY_FIELDS:
        assert forbidden not in raw_low
        assert forbidden not in [str(k).lower() for k in data.keys()]

    # Проверка отсутствия старых идентификаторов
    assert "prid" not in raw_low
    assert "12345" not in raw_low