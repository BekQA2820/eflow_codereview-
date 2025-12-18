# conftest.py
import os
import json
import hashlib
import pytest
import requests
import redis
import boto3
from botocore.config import Config
from jsonschema import validate, ValidationError
from unittest.mock import Mock

# ============================================================
# Base API config
# ============================================================

BASE_URL = os.getenv("BASE_URL", "https://dev-eflow-api.astrazenecacloud.ru")
API_PREFIX = os.getenv("API_PREFIX", "/api/v1")
FULL_BASE = BASE_URL.rstrip("/") + API_PREFIX

# ============================================================
# External services config
# ============================================================

REDIS_URL = os.getenv("REDIS_URL")

S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_BUCKET = os.getenv("S3_BUCKET", "widgets-config")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "ru-central1")

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
# API client (SAFE)
# ============================================================

@pytest.fixture
def api_client():
    class API:
        def __init__(self, base_url: str):
            self.base = base_url.rstrip("/")

        def _url(self, path: str) -> str:
            return f"{self.base}{path}"

        def get(self, path, headers=None, params=None):
            return requests.get(self._url(path), headers=headers or {}, params=params, timeout=10)

        def post(self, path, json=None, headers=None):
            return requests.post(self._url(path), json=json, headers=headers or {}, timeout=10)

        def put(self, path, json=None, headers=None):
            return requests.put(self._url(path), json=json, headers=headers or {}, timeout=10)

        def patch(self, path, json=None, headers=None):
            return requests.patch(self._url(path), json=json, headers=headers or {}, timeout=10)

        def delete(self, path, headers=None):
            return requests.delete(self._url(path), headers=headers or {}, timeout=10)

    return API(FULL_BASE)

# ============================================================
# Auth tokens and headers
# ============================================================

@pytest.fixture(scope="session")
def token_valid():
    return os.getenv("TEST_TOKEN_VALID")

@pytest.fixture(scope="session")
def token_other_user():
    return os.getenv("TEST_TOKEN_OTHER", "other.user.token")

@pytest.fixture(scope="session")
def token_admin():
    return os.getenv("TEST_TOKEN_ADMIN", "admin.token")

@pytest.fixture(scope="session")
def token_employee():
    return os.getenv("TEST_TOKEN_EMPLOYEE", "employee.token")

@pytest.fixture
def auth_headers(token_valid):
    if not token_valid:
        pytest.skip("TEST_TOKEN_VALID is not set")
    return {"Authorization": f"Bearer {token_valid}"}

@pytest.fixture
def auth_header(auth_headers):
    return auth_headers

@pytest.fixture
def auth_header_other_user(token_other_user):
    return {"Authorization": f"Bearer {token_other_user}"}

@pytest.fixture
def auth_header_factory():
    def _factory(token: str):
        return {"Authorization": f"Bearer {token}"}
    return _factory

@pytest.fixture
def admin_token(token_admin):
    return token_admin

@pytest.fixture
def employee_token(token_employee):
    return token_employee

@pytest.fixture
def invalid_auth_headers():
    return {"Authorization": "Bearer invalid.token.value"}

@pytest.fixture
def valid_prid():
    return "00000000-0000-0000-0000-000000000001"

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
# Redis mock and alias
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

@pytest.fixture
def redis_client(mock_redis):
    return mock_redis

# ============================================================
# S3 mock and alias
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

@pytest.fixture
def s3_client(mock_s3):
    return mock_s3

@pytest.fixture
def mock_s3_fail(mocker):
    mocker.patch("boto3.session.Session.client", side_effect=Exception("S3 unavailable"))
    return True

# ============================================================
# Network control
# ============================================================

@pytest.fixture
def allow_requests(mocker):
    """
    Явное разрешение сетевых вызовов через mocker.patch в тесте
    """
    return mocker

@pytest.fixture(autouse=True)
def block_real_network(mocker):
    """
    Запрещает любые реальные HTTP вызовы.
    Тест обязан явно замокать requests.*
    """
    def _blocked(*args, **kwargs):
        raise RuntimeError("REAL NETWORK CALL IS BLOCKED. USE MOCK.")

    mocker.patch("requests.get", side_effect=_blocked)
    mocker.patch("requests.post", side_effect=_blocked)
    mocker.patch("requests.put", side_effect=_blocked)
    mocker.patch("requests.patch", side_effect=_blocked)
    mocker.patch("requests.delete", side_effect=_blocked)
    mocker.patch("requests.head", side_effect=_blocked)
