import json
import re
import pytest

MANIFEST_PATH = "/api/v1/manifest"

ETAG_RE = re.compile(r"^[0-9a-f]{32}$")

DENY_FIELDS = {
    "internalFlags",
    "internalId",
    "debugInfo",
    "backendOnly",
    "serviceRouting",
    "internalMeta",
    "requiredPermissions",
    "configSource",
}


def assert_no_html_and_deny(obj):
    raw = json.dumps(obj, ensure_ascii=False).lower()
    assert "<html" not in raw
    assert "<script" not in raw
    assert "stacktrace" not in raw
    for f in DENY_FIELDS:
        assert f.lower() not in raw


def test_manifest_if_none_match_returns_304(mocker, api_client):
    """
    API CACHE 011
    При неизменном контенте:
    GET + If-None-Match → 304
    Без тела, со строгими заголовками
    """

    etag = "a" * 32

    # ---------- первый ответ (200) ----------
    r1 = mocker.Mock()
    r1.status_code = 200
    r1.headers = {
        "Content-Type": "application/json",
        "ETag": etag,
        "Last-Modified": "Wed, 11 Dec 2025 12:00:00 GMT",
        "Cache-Control": "private, max-age=300",
        "Vary": "Authorization, X-Roles",
        "X-Cache": "MISS",
        "X-Request-ID": "req-1",
    }
    r1.json.return_value = {"layout": {}, "widgets": []}
    r1.text = json.dumps(r1.json.return_value)

    # ---------- второй ответ (304) ----------
    r2 = mocker.Mock()
    r2.status_code = 304
    r2.headers = {
        "ETag": etag,
        "Cache-Control": "private, max-age=300",
        "Vary": "Authorization, X-Roles",
        "X-Request-ID": "req-2",
    }
    r2.text = ""
    r2.content = b""

    mocker.patch("requests.get", side_effect=[r1, r2])

    # ---------- первый запрос ----------
    resp1 = api_client.get(MANIFEST_PATH)

    assert resp1.status_code == 200
    assert resp1.headers["ETag"] == etag
    assert ETAG_RE.match(resp1.headers["ETag"])
    assert resp1.headers.get("Vary") == "Authorization, X-Roles"

    # ---------- второй запрос с If-None-Match ----------
    resp2 = api_client.get(
        MANIFEST_PATH,
        headers={"If-None-Match": etag},
    )

    assert resp2.status_code == 304

    # ---------- тело отсутствует ----------
    assert resp2.text == "" or resp2.content == b""

    # ---------- обязательные заголовки ----------
    assert resp2.headers.get("ETag") == etag
    assert ETAG_RE.match(resp2.headers["ETag"])
    assert resp2.headers.get("Vary") == "Authorization, X-Roles"
    assert resp2.headers.get("Cache-Control")
    assert resp2.headers.get("X-Request-ID")

    # ---------- 304 не содержит traceId ----------
    assert "traceId" not in resp2.headers
