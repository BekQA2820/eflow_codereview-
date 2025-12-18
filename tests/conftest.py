# conftest.py
import os
import json
import hashlib
import pytest
import requests
from jsonschema import validate, ValidationError
from unittest.mock import Mock

# ============================================================
# Base API config
# ============================================================

BASE_URL = os.getenv("BASE_URL", "https://dev-eflow-api.astrazenecacloud.ru")
API_PREFIX = os.getenv("API_PREFIX", "/api/v1")
FULL_BASE = BASE_URL.rstrip("/") + API_PREFIX

# ============================================================
# Schemas
# ============================================================

SCHEMAS_DIR = os.path.join(os.path.dirname(__file__), "schemas")
MANIFEST_SCHEMA_PATH = os.path.join(SCHEMAS_DIR, "manifest_schema.json")
PROFILE_SCHEMA_PATH = os.path.join(SCHEMAS_DIR, "profile_schema.json")

# ============================================================
# Roles hash
# ============================================================

def compute_roles_hash(roles: list[str]) -> str:
    normalized = sorted({r.lower() for r in roles if isinstance(r, str)})
    h = hashlib.blake2b(digest_size=16)
    h.update(",".join(normalized).encode("utf-8"))
    return h.hexdigest()

@pytest.fixture
def roles_hash():
    return compute_roles_hash

# ============================================================
# API client (SAFE - only via mocks)
# ============================================================

@pytest.fixture
def api_client():
    class API:
        def __init__(self, base_url: str):
            self.base = base_url.rstrip("/")

        def _url(self, path: str) -> str:
            return f"{self.base}{path}"

        def get(self, path, headers=None, params=None):
            return requests.get(self._url(path), headers=headers or {}, params=params)

        def post(self, path, json=None, headers=None):
            return requests.post(self._url(path), json=json, headers=headers or {})

        def put(self, path, json=None, headers=None):
            return requests.put(self._url(path), json=json, headers=headers or {})

        def patch(self, path, json=None, headers=None):
            return requests.patch(self._url(path), json=json, headers=headers or {})

        def delete(self, path, headers=None):
            return requests.delete(self._url(path), headers=headers or {})

    return API(FULL_BASE)

# ============================================================
# Auth headers
# ============================================================

@pytest.fixture(scope="session")
def token_valid():
    return os.getenv("TEST_TOKEN_VALID")

@pytest.fixture
def auth_headers(token_valid):
    if not token_valid:
        pytest.skip("TEST_TOKEN_VALID is not set")
    return {"Authorization": f"Bearer {token_valid}"}

@pytest.fixture
def invalid_auth_headers():
    return {"Authorization": "Bearer invalid.token.value"}

# backward compatibility
@pytest.fixture
def auth_header(auth_headers):
    return auth_headers

# ============================================================
# JSON schema helpers
# ============================================================

@pytest.fixture
def manifest_schema():
    if not os.path.exists(MANIFEST_SCHEMA_PATH):
        pytest.skip("manifest schema missing")
    with open(MANIFEST_SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture
def profile_schema():
    if not os.path.exists(PROFILE_SCHEMA_PATH):
        pytest.skip("profile schema missing")
    with open(PROFILE_SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)

def assert_json_schema(instance, schema):
    try:
        validate(instance=instance, schema=schema)
    except ValidationError as e:
        pytest.fail(f"JSON Schema validation failed: {e}")

# ============================================================
# Redis mock
# ============================================================

@pytest.fixture
def mock_redis(mocker):
    store = {}

    redis_mock = Mock()
    redis_mock.get.side_effect = lambda k: store.get(k)
    redis_mock.set.side_effect = lambda k, v, ex=None: store.__setitem__(k, v)
    redis_mock.delete.side_effect = lambda k: store.pop(k, None)

    mocker.patch("redis.from_url", return_value=redis_mock)
    return redis_mock

# ============================================================
# S3 mock
# ============================================================

@pytest.fixture
def mock_s3(mocker):
    s3 = Mock()

    data = {
        "widgets": [
            {
                "id": "w1",
                "visible": True,
                "position": {"row": 0, "col": 0, "width": 1},
                "size": {"width": 2, "height": 2},
            }
        ]
    }

    s3.get_object.return_value = {
        "Body": Mock(read=lambda: json.dumps(data).encode("utf-8"))
    }
    s3.head_object.return_value = {}
    s3.put_object.return_value = True

    mocker.patch("boto3.session.Session.client", return_value=s3)
    return s3

# ============================================================
# GLOBAL network block (CRITICAL)
# ============================================================

@pytest.fixture(autouse=True)
def block_real_network(mocker):
    """
    Запрещает любые реальные HTTP-запросы.
    Любой тест ОБЯЗАН явно замокать requests.*
    """

    def blocked(*args, **kwargs):
        raise AssertionError(
            "REAL NETWORK CALL IS BLOCKED. "
            "Use mocker.patch('requests.*') in the test."
        )

    mocker.patch("requests.get", side_effect=blocked)
    mocker.patch("requests.post", side_effect=blocked)
    mocker.patch("requests.put", side_effect=blocked)
    mocker.patch("requests.patch", side_effect=blocked)
    mocker.patch("requests.delete", side_effect=blocked)
    mocker.patch("requests.head", side_effect=blocked)
