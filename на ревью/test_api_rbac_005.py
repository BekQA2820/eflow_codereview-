import hashlib


def compute_roles_hash(roles: list[str]) -> str:
    """
    Локальная копия алгоритма из conftest.py,
    чтобы тест не зависел от импорта conftest как модуля.
    """
    sorted_roles = sorted(role.lower() for role in roles)
    h = hashlib.blake2b(digest_size=16)
    h.update(",".join(sorted_roles).encode("utf-8"))
    return h.hexdigest()


def test_roles_hash_case_insensitive_and_deduplicated():
    """
    roles_hash должен быть:
    - детерминированным
    - регистронезависимым
    - независимым от порядка
    - одинаковым при дублях ролей
    - в формате hex lowercase, длина 32 символа
    """
    sets = [
        ["employee", "admin"],
        ["admin", "employee"],
        ["Admin", "ADMIN", "employee"],
        ["employee", "admin", "admin"],
    ]

    hashes = [compute_roles_hash(roles) for roles in sets]

    # значения должны совпадать
    assert len(set(hashes)) == 1

    h = hashes[0]
    assert isinstance(h, str)
    assert len(h) == 32
    assert h == h.lower()
    # только hex-символы
    int(h, 16)  # не должно бросить исключение
