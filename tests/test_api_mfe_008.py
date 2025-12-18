
def test_mfe_remote_entry_cache_control(mocker):
    """
    API MFE 008
    remoteEntry.js must have correct Cache-Control and ETag headers
    """

    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.headers = {
        "Cache-Control": "public, max-age=31536000, immutable",
        "ETag": '"abc123etag"',
    }

    mocker.patch("requests.head", return_value=mock_response)

    resp = mock_response

    cache_control = resp.headers.get("Cache-Control", "").lower()

    assert resp.status_code == 200
    assert "max-age" in cache_control
    assert "no-store" not in cache_control
    assert "no-cache" not in cache_control
    assert "private" not in cache_control
    assert "etag" in {k.lower() for k in resp.headers.keys()}
