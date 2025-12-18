import json

MANIFEST_PATH = "/api/v1/manifest"


def test_manifest_field_order_is_stable(mocker, api_client):
    body = {
        "widgets": [
            {
                "id": "w1",
                "type": "mfe",
                "visible": True,
                "mfe": "https://cdn.example.com/app",
                "position": {"row": 0, "col": 0, "width": 1},
            }
        ],
        "layout": {"rows": 1, "columns": 1, "gridType": "fixed"},
        "version": "1",
        "generatedAt": "2025-01-01T00:00:00.000Z",
    }

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/json"}
    resp.text = json.dumps(body)
    resp.json.return_value = body

    mocker.patch("requests.get", return_value=resp)

    r1 = api_client.get(MANIFEST_PATH)
    r2 = api_client.get(MANIFEST_PATH)
    r3 = api_client.get(MANIFEST_PATH)

    assert r1.text == r2.text == r3.text, "порядок полей JSON должен быть стабильным"
