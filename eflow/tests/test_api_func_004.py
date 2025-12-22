import json

CONFIG_PATH = "/api/v1/user/config"
MANIFEST_PATH = "/api/v1/manifest"


def test_put_user_config_idempotent(mocker, api_client):
    config_body = {
        "id": "widget-a",
        "row": 0,
        "col": 0,
        "width": 2,
    }

    put_resp = mocker.Mock()
    put_resp.status_code = 204
    put_resp.headers = {"X-Request-ID": "req-put"}
    put_resp.text = ""

    manifest_resp = mocker.Mock()
    manifest_resp.status_code = 200
    manifest_resp.headers = {"Content-Type": "application/json"}
    manifest_resp.json.return_value = {
        "widgets": [
            {
                "id": "widget-a",
                "type": "mfe",
                "position": {"row": 0, "col": 0, "width": 2},
                "visible": True,
            }
        ],
        "layout": {"rows": 1, "columns": 4, "gridType": "fixed"},
        "version": "1",
    }

    mocker.patch("requests.put", return_value=put_resp)
    mocker.patch("requests.get", return_value=manifest_resp)

    r1 = api_client.put(CONFIG_PATH, json=config_body)
    r2 = api_client.put(CONFIG_PATH, json=config_body)

    assert r1.status_code in (200, 204)
    assert r2.status_code in (200, 204)

    manifest = api_client.get(MANIFEST_PATH).json()
    assert manifest["widgets"][0]["id"] == "widget-a"
