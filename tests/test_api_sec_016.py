MANIFEST_PATH = "/api/v1/manifest"

HTML_TAGS = ("<script", "<img", "<iframe", "<html", "<body")


def _walk_strings(node):
    if isinstance(node, dict):
        for v in node.values():
            yield from _walk_strings(v)
    elif isinstance(node, list):
        for i in node:
            yield from _walk_strings(i)
    elif isinstance(node, str):
        yield node


def test_manifest_contains_no_html_anywhere(mocker, api_client):
    manifest = {
        "widgets": [
            {
                "id": "safe-widget",
                "type": "mfe",
                "title": "Safe title",
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
        lowered = s.lower()
        for tag in HTML_TAGS:
            assert tag not in lowered
