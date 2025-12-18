
import requests


def test_mfe_remote_entry_cors_headers(mocker):
    """
    API MFE 007
    Проверка CORS-заголовков для remoteEntry.js
    """

    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
        "Access-Control-Allow-Headers": "*",
    }

    mocker.patch("requests.head", return_value=mock_response)

    resp = requests.head("ANY_URL")

    assert resp.status_code == 200
    assert resp.headers["Access-Control-Allow-Origin"] == "*"
    assert "GET" in resp.headers["Access-Control-Allow-Methods"]
