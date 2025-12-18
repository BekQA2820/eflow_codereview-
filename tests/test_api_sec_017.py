import re

MANIFEST_PATH = "/api/v1/manifest"

EMAIL_RE = re.compile(r".+@.+\..+")
PHONE_RES = [
    re.compile(r"\+7\d{10}"),
    re.compile(r"\+1\d{10,12}"),
    re.compile(r"\+44\d{9,10}"),
    re.compile(r"\b8\d{10}\b"),
    re.compile(r"\b\d{10,15}\b"),
]


def _walk_strings(node):
    if isinstance(node, dict):
        for v in node.values():
            yield from _walk_strings(v)
    elif isinstance(node, list):
        for i in node:
            yield from _walk_strings(i)
    elif isinstance(node, str):
        yield node


def test_manifest_contains_no_pii_patterns(mocker, api_client):
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

    for s in _walk_strings(r.json()):
        assert not EMAIL_RE.search(s)
        for phone_re in PHONE_RES:
            assert not phone_re.search(s)
