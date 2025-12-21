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
# API client
# ============================================================

@pytest.fixture
def api_client():
    class API:
        def __init__(self, base_url: str):
            self.base = base_url.rstrip("/")

        def _url(self, path: str) -> str:
            return f"{self.base}{path}"

        def request(self, method, path, **kwargs):
            # Используем requests.Session().request или напрямую, 
            # но block_real_network ниже теперь это пропустит
            return requests.request(
                method=method,
                url=self._url(path),
                timeout=10,
                **kwargs,
            )

        def get(self, path, headers=None, params=None):
            return self.request("GET", path, headers=headers or {}, params=params)

        def post(self, path, json=None, headers=None):
            return self.request("POST", path, headers=headers or {}, json=json)

        def put(self, path, json=None, headers=None):
            return self.request("PUT", path, headers=headers or {}, json=json)

        def patch(self, path, json=None, headers=None):
            return self.request("PATCH", path, headers=headers or {}, json=json)

        def delete(self, path, headers=None):
            return self.request("DELETE", path, headers=headers or {})

    return API(FULL_BASE)

# ============================================================
# Auth
# ============================================================

@pytest.fixture(scope="session")
def token_valid():
    token = os.getenv("TEST_TOKEN_VALID")
    if not token:
        # Для локальных тестов или если забыли прокинуть переменную
        return "default_debug_token"
    return token

@pytest.fixture
def auth_headers(token_valid):
    return {"Authorization": f"Bearer {token_valid}"}

@pytest.fixture
def auth_header(auth_headers):
    return auth_headers

@pytest.fixture
def valid_prid():
    """Фикстура для тестов профиля (например, test_profile_xss.py)"""
    return "test-profile-id-123"

# ============================================================
# S3 Mocks
# ============================================================

@pytest.fixture
def s3_client():
    """Фикстура s3_client для тестов RBAC"""
    mock_s3 = Mock()
    return mock_s3

@pytest.fixture
def mock_s3_fail(mocker):
    """Фикстура для эмуляции ошибки S3 (test_api_registry_002.py)"""
    mock = Mock()
    mock.get_object.side_effect = Exception("S3 Service Unavailable")
    mocker.patch("boto3.client", return_value=mock)
    return mock

# ============================================================
# GLOBAL network safety (UPDATED)
# ============================================================

@pytest.fixture(autouse=True)
def block_real_network(mocker):
    """
    Запрещает реальные запросы, КРОМЕ запросов к нашему API.
    """
    original_request = requests.request

    def _smart_block(method, url, **kwargs):
        # Если запрос идет к нашему тестовому стенду - разрешаем
        if BASE_URL in url:
            return original_request(method, url, **kwargs)
        # Все остальные внешние вызовы (google.com и т.д.) блокируем
        raise RuntimeError(f"REAL NETWORK CALL IS BLOCKED to {url}. USE MOCK.")

    mocker.patch("requests.request", side_effect=_smart_block)

# ============================================================
# Redis mock & Schema helpers (остальное без изменений)
# ============================================================

@pytest.fixture
def redis_client():
    store = {}
    redis_mock = Mock()
    redis_mock.get.side_effect = lambda k: store.get(k)
    redis_mock.set.side_effect = lambda k, v, ex=None: store.__setitem__(k, v)
    redis_mock.delete.side_effect = lambda k: store.pop(k, None)
    return redis_mock

@pytest.fixture
def mock_redis(mocker, redis_client):
    mocker.patch("redis.from_url", return_value=redis_client)
    return redis_client