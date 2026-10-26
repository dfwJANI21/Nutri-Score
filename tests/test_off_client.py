"""Tests for the Open Food Facts client (no real network calls)."""
import urllib.error

import pytest

import off_client
from off_client import OFFError


def test_invalid_barcodes_are_rejected():
    for bad in ["", "abc", "1234567", "1234567890123456", "12345678 "]:
        with pytest.raises(OFFError) as e:
            off_client.get_product(bad)
        assert e.value.code == "invalid_barcode"
        assert e.value.status == 422


def test_unknown_barcode(monkeypatch):
    monkeypatch.setattr(off_client, "_get_json", lambda url: {"status": 0})
    with pytest.raises(OFFError) as e:
        off_client.get_product("12345678")
    assert e.value.code == "not_found" and e.value.status == 404


def test_missing_nutrients_stay_none_not_zero(monkeypatch):
    raw = {"status": 1, "product": {"nutriments": {"sugars_100g": 5, "proteins_100g": "2.5"}}}
    monkeypatch.setattr(off_client, "_get_json", lambda url: raw)
    p = off_client.get_product("12345678")
    assert p.nutrition.sugars_g == 5
    assert p.nutrition.proteins_g == 2.5
    assert p.nutrition.salt_g is None
    assert "salt" in p.missing_nutrients
    assert "sugars" not in p.missing_nutrients


def test_source_grade_accepts_only_a_to_e(monkeypatch):
    monkeypatch.setattr(off_client, "_get_json", lambda url: {"status": 1, "product": {"nutrition_grades": "C"}})
    assert off_client.get_product("12345678").off_nutriscore_grade == "c"
    monkeypatch.setattr(off_client, "_get_json", lambda url: {"status": 1, "product": {"nutrition_grades": "unknown"}})
    assert off_client.get_product("12345678").off_nutriscore_grade is None


def test_timeout_becomes_structured_error(monkeypatch):
    def boom(*args, **kwargs):
        raise TimeoutError()
    monkeypatch.setattr(off_client.urllib.request, "urlopen", boom)
    with pytest.raises(OFFError) as e:
        off_client._get_json("https://example.invalid")
    assert e.value.code == "unreachable" and e.value.status == 504


def test_http_error_becomes_structured_error(monkeypatch):
    def boom(*args, **kwargs):
        raise urllib.error.HTTPError("https://example.invalid", 500, "server error", None, None)
    monkeypatch.setattr(off_client.urllib.request, "urlopen", boom)
    with pytest.raises(OFFError) as e:
        off_client._get_json("https://example.invalid")
    assert e.value.code == "http_error" and e.value.status == 502


def test_malformed_json_becomes_structured_error(monkeypatch):
    class FakeResponse:
        def read(self):
            return b"<html>not json</html>"
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
    monkeypatch.setattr(off_client.urllib.request, "urlopen", lambda *a, **k: FakeResponse())
    with pytest.raises(OFFError) as e:
        off_client._get_json("https://example.invalid")
    assert e.value.code == "bad_response"


def test_search_query_length_is_validated():
    with pytest.raises(OFFError) as e:
        off_client.search_products("a")
    assert e.value.code == "invalid_query"


def test_search_skips_results_without_barcode_and_joins_brand_lists(monkeypatch):
    fake = {"hits": [{"code": "1234567890123", "product_name": "X", "brands": ["A", "B"]},
                     {"product_name": "no barcode"}], "count": 2}
    monkeypatch.setattr(off_client, "_get_json", lambda url: fake)
    r = off_client.search_products("test")
    assert len(r.results) == 1
    assert r.results[0].brand == "A, B"


def test_search_falls_back_to_legacy_endpoint(monkeypatch):
    calls = []

    def fake(url):
        calls.append(url)
        if "search.openfoodfacts.org" in url:
            raise OFFError("unreachable", "down", 504)
        return {"products": [{"code": "1234567890123", "product_name": "Y"}], "count": 1}

    monkeypatch.setattr(off_client, "_get_json", fake)
    r = off_client.search_products("test")
    assert len(calls) == 2
    assert r.results[0].name == "Y"
