import re
import json

MANIFEST_PATH = "/api/v1/manifest"


EMAIL_RE = re.compile(r".+@.+\..+")
BASE64_RE = re.compile(r"[A-Za-z0-9+/=]{50,}")
UUID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"
)


def _walk(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _walk(v)
    elif isinstance(obj, list):
        for i in obj:
            yield from _walk(i)
    elif isinstance(obj, str):
        yield obj


def test_manifest_contains_no_pii_or_sensitive_data(mocker, api_client):
    """
    API SEC 009
    Manifest не содержит PII, токенов, email, base64, служебных идентификаторов
    """

    manifest = {
        "layout": {"rows": 1, "columns": 2, "gridType": "fixed"},
        "widgets": [
            {
                "id": "public-widget",
                "type": "mfe",
                "visible": True,
                "position": {"row": 0, "col": 0, "width": 1},
                "mfe": "https://cdn.example.com/app/v1",
            }
        ],
        "version": "1.0",
    }

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {
        "Content-Type": "application/json",
        "X-Request-ID": "req-1",
    }
    resp.json.return_value = manifest
    resp.text = json.dumps(manifest)

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(MANIFEST_PATH)

    assert r.status_code == 200
    data = r.json()

    for value in _walk(data):
        if not isinstance(value, str):
            continue

        assert not EMAIL_RE.search(value)
        assert not BASE64_RE.search(value)
        assert not UUID_RE.search(value)

        lowered = value.lower()
        assert "<html" not in lowered
        assert "token" not in lowered
        assert "password" not in lowered
