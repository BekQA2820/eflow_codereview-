MANIFEST_PATH = "/api/v1/manifest"


def test_layout_gap_and_padding_format(mocker, api_client):
    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/json"}
    resp.json.return_value = {
        "widgets": [],
        "layout": {
            "rows": 1,
            "columns": 1,
            "gridType": "fixed",
            "gap": 8,
            "padding": 16,
        },
        "version": "1",
    }

    mocker.patch("requests.get", return_value=resp)

    layout = api_client.get(MANIFEST_PATH).json()["layout"]

    if "gap" in layout:
        assert isinstance(layout["gap"], int)
        assert layout["gap"] >= 0

    if "padding" in layout:
        assert isinstance(layout["padding"], int)
        assert layout["padding"] >= 0
