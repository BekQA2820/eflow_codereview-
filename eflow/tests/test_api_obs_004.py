import uuid

MANIFEST_PATH = "/api/v1/manifest"


def test_x_request_id_present_and_unique(mocker, api_client):
    def make_response():
        resp = mocker.Mock()
        resp.status_code = 200
        resp.headers = {
            "Content-Type": "application/json",
            "X-Request-ID": str(uuid.uuid4()),
        }
        resp.json.return_value = {
            "widgets": [],
            "layout": {"rows": 0, "columns": 0, "gridType": "fixed"},
            "version": "1",
        }
        return resp

    mocker.patch(
        "requests.get",
        side_effect=[make_response(), make_response(), make_response()],
    )

    ids = []

    for _ in range(3):
        r = api_client.get(MANIFEST_PATH)
        assert r.status_code == 200
        assert "X-Request-ID" in r.headers
        ids.append(r.headers["X-Request-ID"])

    assert len(set(ids)) == 3
