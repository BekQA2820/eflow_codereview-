import json

CONFIG_PATH = "/api/v1/user/config"
MANIFEST_PATH = "/api/v1/manifest"


def test_put_config_width_exceeds_layout_columns(mocker, api_client):
    manifest_resp = mocker.Mock()
    manifest_resp.status_code = 200
    manifest_resp.headers = {"Content-Type": "application/json"}
    manifest_resp.json.return_value = {
        "layout": {"rows": 2, "columns": 12, "gridType": "fixed"},
        "widgets": [],
        "version": "1",
    }

    error_body = {
        "code": "VALIDATION_ERROR",
        "message": "Invalid width",
        "details": [
            {
                "field": "width",
                "message": "must be <= layout.columns",
            }
        ],
        "traceId": "trace-func-007",
    }

    put_resp = mocker.Mock()
    put_resp.status_code = 400
    put_resp.headers = {
        "Content-Type": "application/json",
        "X-Request-ID": "trace-func-007",
        "Cache-Control": "no-store",
    }
    put_resp.json.return_value = error_body
    put_resp.text = json.dumps(error_body)

    mocker.patch("requests.get", return_value=manifest_resp)
    mocker.patch("requests.put", return_value=put_resp)

    manifest = api_client.get(MANIFEST_PATH).json()
    assert manifest["layout"]["columns"] == 12

    r = api_client.put(
        CONFIG_PATH,
        json={"id": "widget-a", "row": 0, "col": 0, "width": 99},
    )

    assert r.status_code == 400
    data = r.json()

    assert data["code"] == "VALIDATION_ERROR"
    assert data["traceId"] == r.headers["X-Request-ID"]
