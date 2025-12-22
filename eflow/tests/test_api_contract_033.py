MANIFEST_PATH = "/api/v1/manifest"


def test_version_changes_after_registry_update(mocker, api_client):
    resp_v1 = mocker.Mock()
    resp_v1.status_code = 200
    resp_v1.headers = {"Content-Type": "application/json"}
    resp_v1.json.return_value = {
        "version": "1",
        "widgets": [],
        "layout": {"rows": 0, "columns": 0, "gridType": "fixed"},
    }

    resp_v2 = mocker.Mock()
    resp_v2.status_code = 200
    resp_v2.headers = {"Content-Type": "application/json"}
    resp_v2.json.return_value = {
        "version": "2",
        "widgets": [],
        "layout": {"rows": 0, "columns": 0, "gridType": "fixed"},
    }

    mocker.patch("requests.get", side_effect=[resp_v1, resp_v2])

    r1 = api_client.get(MANIFEST_PATH)
    r2 = api_client.get(MANIFEST_PATH)

    v1 = r1.json()["version"]
    v2 = r2.json()["version"]

    assert v1 != v2
    assert isinstance(v1, (str, int))
    assert isinstance(v2, (str, int))
