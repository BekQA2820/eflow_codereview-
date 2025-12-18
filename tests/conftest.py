import os

import json

import pytest

import requests

from dotenv import load_dotenv
 
load_dotenv()
 
# =========================

# ENV

# =========================
 
BASE_URL = os.getenv("BASE_URL", "http://localhost")

API_PREFIX = os.getenv("API_PREFIX", "")

FULL_BASE = f"{BASE_URL}{API_PREFIX}".rstrip("/")
 
TEST_TOKEN_VALID = os.getenv("TEST_TOKEN_VALID")

TEST_TOKEN_INVALID = os.getenv("TEST_TOKEN_INVALID")
 
# =========================

# API CLIENT

# =========================
 
class API:

    def __init__(self, base: str):

        self.base = base.rstrip("/")
 
    def get(self, path: str, headers: dict | None = None):

        return requests.get(

            f"{self.base}{path}",

            headers=headers or {},

            timeout=10,

        )
 
    def put(self, path: str, json_body: dict | None = None, headers: dict | None = None):

        return requests.put(

            f"{self.base}{path}",

            json=json_body,

            headers=headers or {},

            timeout=10,

        )
 
# =========================

# FIXTURES

# =========================
 
@pytest.fixture

def api_client():

    return API(FULL_BASE)
 
 
@pytest.fixture

def auth_headers():

    if not TEST_TOKEN_VALID:

        pytest.skip("TEST_TOKEN_VALID is not set")
 
    return {

        "Authorization": f"Bearer {TEST_TOKEN_VALID}",

        "Content-Type": "application/json",

    }
 
 
@pytest.fixture

def invalid_auth_headers():

    if not TEST_TOKEN_INVALID:

        pytest.skip("TEST_TOKEN_INVALID is not set")
 
    return {

        "Authorization": f"Bearer {TEST_TOKEN_INVALID}",

        "Content-Type": "application/json",

    }
 
# =========================

# HELPERS

# =========================
 
def compute_roles_hash(roles: list[str]) -> str:

    """

    Утилита для RBAC тестов

    """

    import hashlib
 
    normalized = ",".join(sorted(roles))

    return hashlib.sha256(normalized.encode()).hexdigest()
 
 
@pytest.fixture

def roles_hash():

    def _inner(roles: list[str]):

        return compute_roles_hash(roles)
 
    return _inner

 