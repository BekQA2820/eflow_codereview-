import re
import pytest
import allure


def _assert_uuid(v: str):
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        v,
    ), f"traceId is not UUID: {v!r}"


def _lower(s):
    return (s or "").lower()


@allure.epic("Profile")
@allure.feature("Contract")
@pytest.mark.integration
def test_profile_proto_008_array_item_with_unknown_field_rejected(api_client):
    """
    PROFILE PROTO 008
    Реальный тест: неизвестные поля внутри элементов массива должны отклоняться ErrorResponse.
    """

    payload = {
        "displayName": "Ivan",
        "phones": [
            {"value": "+79990000000", "internal": True},  # неизвестное поле
        ],
    }

    r = api_client.post(
        "/api/v1/profiles",
        json=payload,
    )

    assert r.status_code in (400, 422), f"Expected 400/422, got {r.status_code}, body={r.text[:300]!r}"

    ct = r.headers.get("Content-Type", "")
    assert "application/json" in ct, f"Unexpected Content-Type: {ct!r}"

    body = r.json()
    assert isinstance(body, dict), f"ErrorResponse must be object, got {type(body)}"

    # Обязательные поля ErrorResponse
    assert body.get("code"), "Missing code"
    assert body.get("message"), "Missing message"
    assert body.get("traceId"), "Missing traceId"

    # traceId + correlation
    _assert_uuid(body["traceId"])
    xrid = r.headers.get("X-Request-ID")
    assert xrid, "Missing X-Request-ID"
    assert xrid == body["traceId"], "X-Request-ID must equal body.traceId"

    # Семантика
    assert body["code"] in ("FIELD_NOT_ALLOWED", "VALIDATION_ERROR", "BAD_REQUEST"), f"Unexpected code: {body['code']!r}"

    # details: phones[0].internal
    details = body.get("details")
    if details is not None:
        assert isinstance(details, list), "details must be list when present"

        # допускаем, что бэкенд может возвращать другой формат field (например phones.0.internal),
        # но мы все равно ожидаем явное упоминание пути.
        details_fields = []
        for d in details:
            if isinstance(d, dict) and "field" in d:
                details_fields.append(str(d.get("field")))

        assert any(
            f in ("phones[0].internal", "phones.0.internal", "phones[0].internalFlag") or "phones" in f and "internal" in f
            for f in details_fields
        ), f"details must mention phones[0].internal, got fields={details_fields!r}"

        assert any((d or {}).get("code") == "NOT_ALLOWED" for d in details if isinstance(d, dict)), "details must include NOT_ALLOWED"

    # Кэш инварианты для 4xx (не супер жестко)
    cc = (r.headers.get("Cache-Control") or "").lower()
    if cc:
        assert "no-store" in cc or "no-cache" in cc, f"Unexpected Cache-Control for 4xx: {cc!r}"

    vary = r.headers.get("Vary")
    if vary:
        assert "authorization" in vary.lower(), f"Vary should include Authorization when present, got: {vary!r}"

    # Антиутечки/без HTML
    text_l = _lower(r.text)
    deny = ["<html", "stacktrace", "exception", "debuginfo", "internalid", "internalflags", "internalmeta"]
    assert not any(x in text_l for x in deny), "Response contains forbidden debug/html content"
