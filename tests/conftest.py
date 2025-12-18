import os
import json
import pytest
import requests
from dotenv import load_dotenv

load_dotenv()

# =========================
# CONFIG
# =========================

BASE_URL = os.getenv(
    "BASE_URL",
    "https://dev-eflow-api.astrazenecacloud.ru",
).rstrip("/")

API_PREFIX = "/api/v1"

TEST_TOKEN_VALID = os.getenv("TEST_TOKEN_VALID")

# =========================
# NETWORK BLOCKER
# =========================

@pytest.fixture(autouse=True)
def block_real_http_calls(monkeypatch):
    """
    Блокирует любые реальные HTTP вызовы.
    Любой запрос без mock приводит к явному падению теста.
    """

    def _blocked(*args, **kwargs):
        raise RuntimeError(
            "REAL NETWORK CALL IS BLOCKED. USE MOCK."
        )

    monkeypatch.setattr(requests, "request", _blocked)
    monkeypatch.setattr(requests, "get", _blocked)
    monkeypatch.setattr(requests, "post", _blocked)
    monkeypatch.setattr(requests, "patch", _blocked)
    monkeypatch.setattr(requests, "put", _blocked)
    monkeypatch.setattr(requests, "delete", _blocked)
    monkeypatch.setattr(requests, "head", _blocked)


# =========================
# API CLIENT
# =========================

@pytest.fixture
def api_client():
    class API:
        def _url(self, path: str) -> str:
            if not path.startswith("/"):
                path = "/" + path

            # path может быть уже с /api/v1
            if path.startswith(API_PREFIX):
                return f"{BASE_URL}{path}"

            return f"{BASE_URL}{API_PREFIX}{path}"

        def get(self, path, headers=None, params=None):
            return requests.request(
                "GET",
                self._url(path),
                headers=headers or {},
                params=params,
                timeout=10,
            )

        def post(self, path, json=None, headers=None):
            return requests.request(
                "POST",
                self._url(path),
                headers=headers or {},
                json=json,
                timeout=10,
            )

        def patch(self, path, json=None, headers=None):
            return requests.request(
                "PATCH",
                self._url(path),
                headers=headers or {},
                json=json,
                timeout=10,
            )

        def put(self, path, json=None, headers=None):
            return requests.request(
                "PUT",
                self._url(path),
                headers=headers or {},
                json=json,
                timeout=10,
            )

        def delete(self, path, headers=None):
            return requests.request(
                "DELETE",
                self._url(path),
                headers=headers or {},
                timeout=10,
            )

    return API()


# =========================
# AUTH FIXTURES
# =========================

@pytest.fixture
def token_valid():
    if not TEST_TOKEN_VALID:
        pytest.skip("TEST_TOKEN_VALID is not set")
    return TEST_TOKEN_VALID


@pytest.fixture
def auth_header(token_valid):
    return {"Authorization": f"Bearer {token_valid}"}


@pytest.fixture
def auth_header_factory():
    def _factory(roles):
        token = str(roles)
        return {"Authorization": f"Bearer {token}"}
    return _factory


@pytest.fixture
def auth_header_other_user():
    return {"Authorization": "Bearer other.user.token"}


@pytest.fixture
def employee_token():
    return "employee.token"


@pytest.fixture
def admin_token():
    return "admin.token"


# =========================
# HELPERS
# =========================

@pytest.fixture
def json_response_factory(mocker):
    def _factory(
        status=200,
        body=None,
        headers=None,
        etag=None,
    ):
        resp = mocker.Mock()
        resp.status_code = status

        final_headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            "Vary": "Authorization",
        }

        if headers:
            final_headers.update(headers)

        if etag:
            final_headers["ETag"] = etag

        if "X-Request-ID" not in final_headers:
            final_headers["X-Request-ID"] = "test-trace-id"

        resp.headers = final_headers
        resp.json.return_value = body or {}
        resp.content = json.dumps(body or {}).encode("utf-8")

        return resp

    return _factory
