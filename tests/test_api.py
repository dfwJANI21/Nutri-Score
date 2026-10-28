"""Tests for the FastAPI routes (the Open Food Facts client is faked)."""
from fastapi.testclient import TestClient

import main
import off_client
import scoring
from models import Nutrition, Product

client = TestClient(main.app)


def fake_product():
    return Product(barcode="12345678", nutrition=Nutrition(), source_url="https://example.invalid")


def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}


def test_invalid_barcode_gives_structured_error():
    r = client.get("/api/product/abc")
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "invalid_barcode"


def test_frontend_is_served():
    r = client.get("/")
    assert r.status_code == 200 and "NutriScore" in r.text


def test_scanner_files_are_served():
    for path in ["/js/scanner.js", "/js/lib/html5-qrcode.min.js"]:
        assert client.get(path).status_code == 200


def test_analysis_unavailable_when_scoring_not_implemented(monkeypatch):
    monkeypatch.setattr(off_client, "get_product", lambda b: fake_product())

    def not_ready(product):
        raise NotImplementedError

    monkeypatch.setattr(scoring, "calculate_nutriscore", not_ready)
    body = client.get("/api/analysis/12345678").json()
    assert body["calculated"]["status"] == "unavailable"
    assert body["calculated"]["grade"] is None


def test_analysis_unavailable_when_data_is_missing(monkeypatch):
    monkeypatch.setattr(off_client, "get_product", lambda b: fake_product())

    def missing(product):
        raise scoring.ScoreUnavailable("salt is missing")

    monkeypatch.setattr(scoring, "calculate_nutriscore", missing)
    body = client.get("/api/analysis/12345678").json()
    assert body["calculated"]["reason"] == "salt is missing"
