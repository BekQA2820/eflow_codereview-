import os
import json
import hashlib
import pytest
import requests
import redis
import boto3
from botocore.config import Config
from jsonschema import validate, ValidationError
 
# ============================================================
# Base API config
# ============================================================
 
BASE_URL = os.getenv("BASE_URL", "https://dev-eflow-api.astrazenecacloud.ru")
API_PREFIX = os.getenv("API_PREFIX", "/api/v1")
FULL_BASE = BASE_URL.rstrip("/") + API_PREFIX
 
# ============================================================
# External services
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
# Utils
# ============================================================
 
def compute_roles_hash(roles: list[str]) -> str:
    normalized = sorted({r.lower() for r in roles if isinstance(r, str)})
    h = hashlib.blake2b(digest_size=16)
    h.update(",".join(normalized).encode("utf-8"))
    return h.hexdigest()
 
# ============================================================
# API client
# ============================================================
 
class API:
    def __init__(self, base_url: str):
        self.base = base_url.rstrip("/")
 
    def get(self, path, headers=None, params=None):
        return requests.get(
            f"{self.base}{path}",
            headers=headers or {},
            params=params,
            timeout=10,
        )
 
    def post(self, path, json_body=None, headers=None):
        return requests.post(
            f"{self.base}{path}",
            json=json_body,
            headers=headers or {},
            timeout=10,
        )
 
    def put(self, path, json_body=None, headers=None):
        return requests.put(
            f"{self.base}{path}",
            json=json_body,
            headers=headers or {},
            timeout=10,
        )
 
    def patch(self, path, json_body=None, headers=None):
        return requests.patch(
            f"{self.base}{path}",
            json=json_body,
            headers=headers or {},
            timeout=10,
        )
 
    def delete(self, path, headers=None):
        return requests.delete(
            f"{self.base}{path}",
            headers=headers or {},
            timeout=10,
        )
 
@pytest.fixture
def api_client():
    return API(FULL_BASE)
 
# ============================================================
# Auth fixtures
# ============================================================
 
@pytest.fixture(scope="session")
def token_valid():
    return os.getenv("TEST_TOKEN_VALID")
 
@pytest.fixture(scope="session")
def token_other_user():
    return os.getenv("TEST_TOKEN_OTHER")
 
@pytest.fixture(scope="session")
def token_expired():
    return os.getenv("TEST_TOKEN_EXPIRED")
 
# ВАЖНО: именно auth_header, как ждут тесты
@pytest.fixture
def auth_header(token_valid):
    if not token_valid:
        pytest.skip("TEST_TOKEN_VALID is not set")
    return {"Authorization": f"Bearer {token_valid}"}
 
@pytest.fixture
def invalid_auth_headers():
    return {"Authorization": "Bearer invalid.token"}
 
# ============================================================
# Redis / S3 real clients
# ============================================================
 
@pytest.fixture(scope="session")
def redis_client():
    if not REDIS_URL:
        pytest.skip("REDIS_URL is not configured")
    return redis.from_url(REDIS_URL, decode_responses=True)
 
@pytest.fixture(scope="session")
def s3_client():
    if not S3_ENDPOINT:
        pytest.skip("S3_ENDPOINT is not configured")
 
    session = boto3.session.Session()
    config = Config(signature_version="s3v4", region_name=AWS_REGION)
 
    return session.client(
        service_name="s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        config=config,
    )
 
# ============================================================
# Schemas fixtures
# ============================================================
 
@pytest.fixture
def manifest_schema():
    if not os.path.exists(MANIFEST_SCHEMA_PATH):
        pytest.skip("manifest_schema.json missing")
    with open(MANIFEST_SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)
 
@pytest.fixture
def profile_schema():
    if not os.path.exists(PROFILE_SCHEMA_PATH):
        pytest.skip("profile_schema.json missing")
    with open(PROFILE_SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)
 
def assert_json_schema(instance, schema):
    try:
        validate(instance=instance, schema=schema)
    except ValidationError as e:
        pytest.fail(f"JSON Schema validation failed: {e}")
 
# ============================================================
# Cache helpers
# ============================================================
 
@pytest.fixture
def invalidate_cache(redis_client):
    def _invalidate(key: str):
        redis_client.delete(key)
    return _invalidate
 
# ============================================================
# MOCKS (используются только в тестах)
# ============================================================
 
@pytest.fixture
def mock_redis(mocker):
    store = {}
 
    redis_mock = mocker.Mock()
    redis_mock.get.side_effect = lambda k: store.get(k)
    redis_mock.set.side_effect = lambda k, v, ex=None: store.__setitem__(k, v)
    redis_mock.delete.side_effect = lambda k: store.pop(k, None)
 
    mocker.patch("redis.from_url", return_value=redis_mock)
    return redis_mock
 
@pytest.fixture
def mock_s3(mocker):
    s3 = mocker.Mock()
 
    data = {
        "widgets": [
            {
                "id": "w1",
                "visible": True,
                "position": {"row": 0, "col": 0},
                "size": {"width": 2, "height": 2},
            }
        ]
    }
 
    def fake_get_object(Bucket, Key):
        return {
            "Body": mocker.Mock(
                read=lambda: json.dumps(data).encode("utf-8")
            )
        }
 
    s3.get_object.side_effect = fake_get_object
    s3.put_object.return_value = True
    s3.head_object.return_value = {}