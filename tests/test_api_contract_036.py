MANIFEST_PATH = "/api/v1/manifest"


def test_widget_id_has_no_spaces_or_whitespace(mocker, api_client):
    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/json"}
    resp.json.return_value = {
        "widgets": [
            {
                "id": "widget-one",
                "type": "mfe",
                "visible": True,
                "mfe": "https://cdn.example.com/app1",
                "position": {"row": 0, "col": 0, "width": 1},
            },
            {
                "id": "widget_two",
                "type": "link",
                "visible": True,
                "position": {"row": 0, "col": 1, "width": 1},
            },
        ],
        "layout": {"rows": 1, "columns": 2, "gridType": "fixed"},
        "version": "1",
    }

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(MANIFEST_PATH)
    data = r.json()

    for idx, w in enumerate(data["widgets"]):
        wid = w.get("id")
        assert isinstance(wid, str)
        assert wid != ""
        assert wid == wid.strip(), f"widget[{idx}].id содержит пробелы по краям"
        assert " " not in wid, f"widget[{idx}].id содержит пробел"
        assert "\t" not in wid, f"widget[{idx}].id содержит табуляцию"
