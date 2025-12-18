import json

MANIFEST_PATH = "/api/v1/manifest"


def test_manifest_json_is_always_parseable(mocker, api_client):
    raw_json = """
    {
        "widgets": [
            {
                "id": "w1",
                "type": "mfe",
                "visible": true,
                "mfe": "https://cdn.example.com/app",
                "position": {"row": 0, "col": 0, "width": 1}
            }
        ],
        "layout": {"rows": 1, "columns": 1, "gridType": "fixed"},
        "version": "1"
    }
    """

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/json"}
    resp.text = raw_json
    resp.json.side_effect = lambda: json.loads(raw_json)

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(MANIFEST_PATH)

    parsed = json.loads(r.text)
    assert isinstance(parsed, dict)
