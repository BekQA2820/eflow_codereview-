import re

MANIFEST_PATH = "/api/v1/manifest"

RE_KB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
RE_SN = re.compile(r"^[a-z0-9]+(_[a-z0-9]+)*$")
RE_UUID = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


def test_widget_id_matches_allowed_formats(mocker, api_client):
    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/json"}
    resp.json.return_value = {
        "widgets": [
            {"id": "widget-main", "type": "mfe", "position": {"row": 0, "col": 0, "width": 1}},
            {"id": "widget_secondary", "type": "link", "position": {"row": 0, "col": 1, "width": 1}},
            {"id": "550e8400-e29b-41d4-a716-446655440000", "type": "empty", "position": {"row": 1, "col": 0, "width": 2}},
        ]
    }

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(MANIFEST_PATH)
    data = r.json()

    for idx, w in enumerate(data["widgets"]):
        wid = w["id"]
        assert isinstance(wid, str), f"widget[{idx}].id must be string"
        assert wid.strip() == wid and wid, f"widget[{idx}].id must be non-empty without spaces"

        assert (
            RE_KB.fullmatch(wid)
            or RE_SN.fullmatch(wid)
            or RE_UUID.fullmatch(wid)
        ), f"widget[{idx}].id has invalid format: {wid}"
