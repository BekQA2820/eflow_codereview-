MANIFEST_PATH = "/api/v1/manifest"


def test_container_widgets_do_not_overlap_and_contain_children(mocker, api_client):
    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/json"}
    resp.json.return_value = {
        "widgets": [
            {
                "id": "container-1",
                "type": "container",
                "visible": True,
                "position": {"row": 0, "col": 0, "width": 4},
                "children": [
                    {
                        "id": "child-1",
                        "type": "mfe",
                        "visible": True,
                        "position": {"row": 0, "col": 0, "width": 2},
                    },
                    {
                        "id": "child-2",
                        "type": "mfe",
                        "visible": True,
                        "position": {"row": 0, "col": 2, "width": 2},
                    },
                ],
            }
        ],
        "layout": {"rows": 1, "columns": 4, "gridType": "fixed"},
        "version": "1",
    }

    mocker.patch("requests.get", return_value=resp)

    data = api_client.get(MANIFEST_PATH).json()
    container = data["widgets"][0]
    cpos = container["position"]

    for child in container["children"]:
        pos = child["position"]
        assert pos["col"] >= cpos["col"]
        assert pos["col"] + pos["width"] <= cpos["col"] + cpos["width"]
