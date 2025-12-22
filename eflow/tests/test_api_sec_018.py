import re

MANIFEST_PATH = "/api/v1/manifest"

IP_RE = re.compile(r"\b\d{1,3}(\.\d{1,3}){3}\b")
UUID_V4_RE = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b"
)

FORBIDDEN_KEYS = {
    "employee_id",
    "eid",
    "hr_id",
    "token",
    "session",
    "access_token",
    "refresh_token",
}


def _walk(node):
    if isinstance(node, dict):
        for k, v in node.items():
            yield k
            yield from _walk(v)
    elif isinstance(node, list):
        for i in node:
            yield from _walk(i)
    elif isinstance(node, str):
        yield node


def test_manifest_contains_no_ip_or_sensitive_ids(mocker, api_client):
    manifest = {
        "widgets": [
            {
                "id": "widget-1",
                "type": "mfe",
                "title": "Dashboard",
                "position": {"row": 0, "col": 0, "width": 1},
            }
        ],
        "layout": {"rows": 1, "columns": 1, "gridType": "fixed"},
        "version": "1",
    }

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/json"}
    resp.json.return_value = manifest

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(MANIFEST_PATH)
    assert r.status_code == 200

    for value in _walk(r.json()):
        if isinstance(value, str):
            assert not IP_RE.search(value)
            assert not UUID_V4_RE.search(value)
            lowered = value.lower()
            for key in FORBIDDEN_KEYS:
                assert key not in lowered
