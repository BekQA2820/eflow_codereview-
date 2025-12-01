import os

import pytest
import string
import random

PROFILE_BASE = "/api/v1/profile"

def rand_text(n):
    return "".join(random.choice(string.ascii_letters + " ") for _ in range(n))

def test_patch_about_me_positive(api_client, auth_header):

    prid = pytest.config.getoption("--prid") if hasattr(pytest, "config") else None
    prid = prid or os.getenv("TEST_PRID")
    assert prid, "TEST_PRID must be set in env or passed as CLI --prid"

    text = "QA autotest about me " + rand_text(20)
    r = api_client.patch(f"{PROFILE_BASE}/{prid}/about-me", json={"about_me": text}, headers=auth_header)
    assert r.status_code == 200
    # верификация апдейта
    g = api_client.get(f"{PROFILE_BASE}/{prid}", headers=auth_header)
    assert g.status_code == 200
    assert g.json().get("about_me") == text

def test_patch_about_me_too_long(api_client, auth_header):
    # 1001 символов
    text = "x" * 1001
    prid = os.getenv("TEST_PRID")
    r = api_client.patch(f"{PROFILE_BASE}/{prid}/about-me", json={"about_me": text}, headers=auth_header)
    assert r.status_code == 400
    body = r.json()
    assert "code" in body and "traceId" in body
    assert isinstance(body.get("details"), list)
