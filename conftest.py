# conftest.py
import os
import hashlib
import json
import time
import pytest
import requests
import redis
import boto3
from botocore.config import Config
from jsonschema import validate, ValidationError

BASE_URL = os.getenv("BASE_URL", "https://dev-eflow-api.astrazenecacloud.ru/login")
API_PREFIX = os.getenv("API_PREFIX", "/api/v1")
FULL_BASE = BASE_URL.rstrip("/") + API_PREFIX

REDIS_URL = os.getenv("REDIS_URL")  # e.g. redis://user:pass@host:6379/0
S3_ENDPOINT = os.getenv("S3_ENDPOINT")  # e.g. https://s3.yandexcloud.net
S3_BUCKET = os.getenv("S3_BUCKET", "widgets-config")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
REGION = os.getenv("AWS_REGION", "ru-central1")

MANIFEST_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schemas", "manifest_schema.json")


def compute_roles_hash(roles: list[str]) -> str:

    sorted_roles = sorted(role.lower() for role in roles)
    h = hashlib.blake2b(digest_size=16)
    h.update(",".join(sorted_roles).encode("utf-8"))
    return h.hexdigest()


@pytest.fixture(scope="session")
def redis_client():
    if not REDIS_URL:
        pytest.skip("REDIS_URL is not configured")
    return redis.from_url(REDIS_URL, decode_responses=True)


@pytest.fixture(scope="session")
def s3_client():
    if not S3_ENDPOINT:
        pytest.skip("S3_ENDPOINT not configured")
    session = boto3.session.Session()
    config = Config(signature_version="s3v4", region_name=REGION)
    client = session.client(
        service_name="s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        config=config,
    )
    return client


@pytest.fixture
def api_client():
    class API:
        def __init__(self, base):
            self.base = base.rstrip("/")

        def get(self, path, headers=None, params=None):
            return requests.get(f"{self.base}{path}", headers=headers or {}, params=params, timeout=10)

        def patch(self, path, json=None, headers=None):
            return requests.patch(f"{self.base}{path}", json=json, headers=headers or {}, timeout=10)

        def post(self, path, json=None, headers=None):
            return requests.post(f"{self.base}{path}", json=json, headers=headers or {}, timeout=10)

        def delete(self, path, headers=None):
            return requests.delete(f"{self.base}{path}", headers=headers or {}, timeout=10)

    return API(BASE_URL.rstrip("/"))


# Фикстуры токена: valid_token, expired_token, userB_token
@pytest.fixture(scope="session")
def token_valid():
    return os.getenv("TEST_TOKEN_VALID")


@pytest.fixture(scope="session")
def token_other_user():
    return os.getenv("TEST_TOKEN_OTHER")  # другие юзеры


@pytest.fixture(scope="session")
def token_expired():
    return os.getenv("TEST_TOKEN_EXPIRED")


@pytest.fixture
def auth_header(token_valid):
    return {"Authorization": f"Bearer {token_valid}"} if token_valid else {}


@pytest.fixture
def manifest_cache_key():
    def _key(prid: str, roles: list):
        return f"manifest:{prid}:{compute_roles_hash(roles)}"
    return _key


@pytest.fixture
def manifest_schema():
    if not os.path.exists(MANIFEST_SCHEMA_PATH):
        pytest.skip("manifest schema missing")
    with open(MANIFEST_SCHEMA_PATH) as f:
        return json.load(f)


def assert_json_schema(instance, schema):
    try:
        validate(instance=instance, schema=schema)
    except ValidationError as e:
        pytest.fail(f"JSON Schema validation failed: {e}")


# редис
@pytest.fixture
def invalidate_cache(redis_client):
    def _invalidate(key):
        redis_client.delete(key)
    return _invalidate
