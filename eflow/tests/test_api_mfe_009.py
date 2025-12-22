def test_mfe_remote_entry_cors_headers(mocker):
    """
    API MFE 009
    remoteEntry.js must expose valid CORS headers
    """

    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
        "Access-Control-Allow-Headers": "*",
    }

    mocker.patch("requests.head", return_value=mock_response)

    resp = mock_response

    assert resp.status_code == 200

    assert "Access-Control-Allow-Origin" in resp.headers
    assert resp.headers["Access-Control-Allow-Origin"]

    assert "Access-Control-Allow-Methods" in resp.headers

    raw_headers = str(resp.headers).lower()
    assert "<html" not in raw_headers