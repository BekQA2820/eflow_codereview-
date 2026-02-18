import json
import os
import hashlib
import pytest
import requests
import urllib3
from unittest.mock import MagicMock


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================
# Настройки окружения
# ============================================================
BASE_URL = os.getenv("BASE_URL", "https://dev-eflow.astrazenecacloud.ru")
API_PREFIX = os.getenv("API_PREFIX", "/gateway")
FULL_BASE = BASE_URL.rstrip("/") + API_PREFIX

AUTH_USER = "max-gorkiy"
AUTH_PASS = "max-gorkiy-TEST-123)"


# ============================================================
# Утилиты
# ============================================================
def compute_roles_hash(roles: list[str]) -> str:
    """
    Вычисляет хэш ролей для нормализации.
    Сортирует роли, приводит к нижнему регистру, создает хэш.
    """
    normalized = sorted({r.lower() for r in roles if isinstance(r, str)})
    h = hashlib.blake2b(digest_size=16)
    h.update(",".join(normalized).encode("utf-8"))
    return h.hexdigest()


@pytest.fixture
def roles_hash():
    """Возвращает функцию для вычисления хэша ролей."""
    return compute_roles_hash


# ============================================================
# АВТОРИЗАЦИЯ (Автоматическое получение JWT)
# ============================================================
@pytest.fixture(scope="session")
def token_valid():
    """
    Получение токена для интеграционных тестов.
    Если токен передан в переменной окружения, используется он, иначе делаем запрос на новый токен.
    """
    env_token = os.getenv("TEST_TOKEN_VALID")
    if env_token and env_token != "default_debug_token":
        print(f"[Auth] Using provided token: {env_token}")
        return env_token

    # Новый процесс получения токена
    auth_url = f"{BASE_URL.rstrip('/')}/gateway/api/v1/auth/login"
    payload = {"username": AUTH_USER, "password": AUTH_PASS}

    print(f"\n[Auth] Trying to login at: {auth_url}")

    try:
        # Запрос на получение токена
        resp = requests.post(auth_url, json=payload, timeout=10, verify=False)
        if resp.status_code == 200:
            data = resp.json()
            token = data.get("access_token") or data.get("token")
            if token:
                print(f"✅ [Auth] Success! Received token (len={len(token)}) for {BASE_URL}")
                return token
            print("❌ [Auth] Status 200, but token key not found in JSON")
        else:
            print(f"❌ [Auth] Failed! Status: {resp.status_code}, Body: {resp.text[:100]}")
    except Exception as e:
        print(f"⚠️ [Auth] Connection error: {e}")

    return "default_debug_token"


# ============================================================
# ГИБРИДНЫЙ API CLIENT (Mock <-> Real)
# ============================================================
@pytest.fixture
def api_client(request, token_valid):
    """
    Фикстура API клиента, который переключается между реальной сетью и моками в зависимости от маркера.
    """

    class API:
        def __init__(self, base_url: str):
            self.base = base_url.rstrip("/")
            self.is_integration = request.node.get_closest_marker("integration") is not None
            self.token = token_valid

        def _url(self, path: str) -> str:
            clean_path = path.lstrip("/")
            if clean_path.startswith("api/v1") and self.base.endswith("api/v1"):
                clean_path = clean_path.replace("api/v1", "", 1).lstrip("/")
            return f"{self.base}/{clean_path}" if not path.startswith("http") else path

        def request(self, method, path, **kwargs):
            url = self._url(path)

            # Автоматическая подстановка токена
            if self.token and self.token != "default_debug_token":
                headers = kwargs.get("headers", {})
                if "Authorization" not in headers:
                    headers["Authorization"] = f"Bearer {self.token}"
                kwargs["headers"] = headers

                # Выводим в лог, что токен используется для запросов
                print(f"[API Client] Using token {self.token[:10]}... for request to {url}")

            # Режим интеграции (реальная сеть)
            if self.is_integration:
                kwargs.setdefault('timeout', 15)
                kwargs.setdefault('verify', False)
                return requests.request(method, url, **kwargs)

            # Режим мока
            if isinstance(requests.request, MagicMock):
                return requests.request(method, url, **kwargs)

            # Дефолтный ответ для мока
            trace_id = kwargs.get('headers', {}).get('X-Request-ID', 'mock-trace-final')
            m = MagicMock(spec=requests.Response)
            m.status_code = 200
            m.headers = {
                "Content-Type": "application/json",
                "X-Request-ID": trace_id,
                "Cache-Control": "public, max-age=3600",
                "X-Cache": "HIT",
                "ETag": '"mock-etag-123"'
            }
            payload = {
                "code": "SUCCESS",
                "profile_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "displayName": "Mock User",
                "traceId": trace_id
            }
            m.json.return_value = payload
            m.text = json.dumps(payload)
            m.content = m.text.encode("utf-8")
            m.ok = True
            return m

        # Удобные методы для HTTP запросов
        def get(self, path, **kwargs):
            return self.request("GET", path, **kwargs)

        def post(self, path, **kwargs):
            return self.request("POST", path, **kwargs)

        def put(self, path, **kwargs):
            return self.request("PUT", path, **kwargs)

        def patch(self, path, **kwargs):
            return self.request("PATCH", path, **kwargs)

        def delete(self, path, **kwargs):
            return self.request("DELETE", path, **kwargs)

    return API(FULL_BASE)


# ============================================================
# Дополнительные фикстуры
# ============================================================
@pytest.fixture
def auth_headers(token_valid):
    """Возвращает заголовки с токеном авторизации"""
    return {"Authorization": f"Bearer {token_valid}"}


@pytest.fixture
def valid_prid():
    """Возвращает валидный ID профиля для тестов"""
    return "3fa85f64-5717-4562-b3fc-2c963f66afa6"


@pytest.fixture
def redis_client():
    """Мок для Redis клиента"""
    store = {}
    redis_mock = MagicMock()
    redis_mock.get.side_effect = lambda k: store.get(k)
    redis_mock.set.side_effect = lambda k, v, ex=None: store.__setitem__(k, v)
    return redis_mock


@pytest.fixture
def s3_client():
    """Мок для S3 клиента"""
    return MagicMock()
