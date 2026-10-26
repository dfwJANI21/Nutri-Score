"""Open Food Facts client: fetches data and turns it into our own models.

AI-assisted file (the API-integration part of the project). Read it, run it, and
make sure you can explain each function. It does NOT calculate any grade.

Only ONE external service is used: Open Food Facts.
  - Barcode lookup : GET {OFF_BASE_URL}/api/v2/product/{barcode}.json?fields=...
  - Name search    : Search-a-licious  GET {OFF_SEARCH_URL}?q=...   (documented, still beta)
                     with the older /cgi/search.pl as a fallback if it fails.
Docs: https://openfoodfacts.github.io/documentation/
"""
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional

from models import Nutrition, Product, SearchHit, SearchResponse

# ---- settings (override with environment variables, no secrets needed) ----
OFF_BASE_URL = os.getenv("OFF_BASE_URL", "https://world.openfoodfacts.org")
OFF_SEARCH_URL = os.getenv("OFF_SEARCH_URL", "https://search.openfoodfacts.org/search")
# Open Food Facts asks for: AppName/Version (contact email). Put YOUR email here.
USER_AGENT = os.getenv("OFF_USER_AGENT", "NutriScoreStudentProject/0.1 (your-email@example.com)")
TIMEOUT_SECONDS = 8
PAGE_SIZE = 12

PRODUCT_FIELDS = (
    "code,product_name,brands,categories,categories_tags,image_front_url,ingredients_text,"
    "quantity,nutriments,nutrition_grades,nutriscore_grade"
)
SEARCH_FIELDS = "code,product_name,brands,categories,image_front_small_url,nutrition_grades"

# nutrient key in our model -> key in the Open Food Facts "nutriments" dict
NUTRIMENT_KEYS = {
    "energy_kcal": "energy-kcal_100g",
    "energy_kj": "energy-kj_100g",
    "fat_g": "fat_100g",
    "saturated_fat_g": "saturated-fat_100g",
    "carbohydrates_g": "carbohydrates_100g",
    "sugars_g": "sugars_100g",
    "fiber_g": "fiber_100g",
    "proteins_g": "proteins_100g",
    "salt_g": "salt_100g",
}
# Where Open Food Facts keeps the fruit/vegetable/legume percentage (label value first, then
# the estimate it computes from the ingredients list). Verify these names on a live product.
FVL_KEYS = ["fruits-vegetables-legumes_100g", "fruits-vegetables-legumes-estimate-from-ingredients_100g"]

# Nutrients reported as "missing" when absent (the ones the Nutri-Score needs)
MISSING_LABELS = {
    "energy_kj": "energy",
    "sugars_g": "sugars",
    "saturated_fat_g": "saturated fat",
    "salt_g": "salt",
    "fiber_g": "fibre",
    "proteins_g": "protein",
    "fruits_veg_legumes_pct": "fruit, vegetable and legume content",
}


class OFFError(Exception):
    """Any problem talking to Open Food Facts. main.py turns it into a JSON error."""

    def __init__(self, code: str, message: str, status: int = 502):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


# ------------------------------------------------------------------ HTTP
def _get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:  # must come before URLError (it is a subclass)
        status = 404 if e.code == 404 else 502
        raise OFFError("http_error", f"Open Food Facts returned HTTP {e.code}.", status) from e
    except (urllib.error.URLError, OSError) as e:  # timeouts and network failures
        raise OFFError("unreachable", "Could not reach Open Food Facts (timeout or network error).", 504) from e
    except (ValueError, UnicodeDecodeError) as e:  # bad JSON
        raise OFFError("bad_response", "Open Food Facts sent a response we could not read.", 502) from e


# ------------------------------------------------------------------ helpers
def _number(value) -> Optional[float]:
    """Return a float, or None. Never turns a missing value into 0."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _text(value) -> Optional[str]:
    """Some fields are a string, a list or a language dict depending on the endpoint."""
    if value is None:
        return None
    if isinstance(value, list):
        value = ", ".join(str(v) for v in value if v)
    elif isinstance(value, dict):
        value = value.get("en") or next(iter(value.values()), None)
    value = str(value).strip() if value is not None else ""
    return value or None


def _grade(value) -> Optional[str]:
    """Source grade as stored by Open Food Facts; only a-e are accepted."""
    g = _text(value)
    return g.lower() if g and g.lower() in {"a", "b", "c", "d", "e"} else None


def validate_barcode(barcode: str) -> str:
    if not re.fullmatch(r"\d{8,14}", barcode or ""):
        raise OFFError("invalid_barcode", "A barcode must be 8 to 14 digits.", 422)
    return barcode


# ------------------------------------------------------------------ normalizing
def normalize_product(raw: dict, barcode: str) -> Product:
    nutriments = raw.get("nutriments") or {}
    values = {field: _number(nutriments.get(key)) for field, key in NUTRIMENT_KEYS.items()}
    values["fruits_veg_legumes_pct"] = next(
        (v for v in (_number(nutriments.get(k)) for k in FVL_KEYS) if v is not None), None)
    nutrition = Nutrition(**values)
    missing = [label for key, label in MISSING_LABELS.items() if values.get(key) is None]
    tags = [t for t in (raw.get("categories_tags") or []) if isinstance(t, str)]
    category = _text(raw.get("categories"))
    return Product(
        barcode=_text(raw.get("code")) or barcode,
        name=_text(raw.get("product_name")),
        brand=_text(raw.get("brands")),
        category=category.split(",")[0].strip() if category else None,
        categories_tags=tags,
        image_url=_text(raw.get("image_front_url")),
        ingredients_text=_text(raw.get("ingredients_text")),
        quantity=_text(raw.get("quantity")),
        nutrition=nutrition,
        off_nutriscore_grade=_grade(raw.get("nutrition_grades") or raw.get("nutriscore_grade")),
        missing_nutrients=missing,
        source_url=f"https://world.openfoodfacts.org/product/{barcode}",
    )


def _to_hit(raw: dict) -> Optional[SearchHit]:
    code = _text(raw.get("code"))
    if not code:
        return None  # a result we cannot open is useless
    category = _text(raw.get("categories"))
    return SearchHit(
        barcode=code,
        name=_text(raw.get("product_name")),
        brand=_text(raw.get("brands")),
        category=category.split(",")[0].strip() if category else None,
        image_url=_text(raw.get("image_front_small_url") or raw.get("image_small_url") or raw.get("image_url")),
        off_nutriscore_grade=_grade(raw.get("nutrition_grades") or raw.get("nutriscore_grade")),
    )


# ------------------------------------------------------------------ public functions
def get_product(barcode: str) -> Product:
    validate_barcode(barcode)
    url = f"{OFF_BASE_URL}/api/v2/product/{barcode}.json?fields={PRODUCT_FIELDS}"
    try:
        data = _get_json(url)
    except OFFError as e:
        if e.status == 404:
            raise OFFError("not_found", "No product with this barcode in Open Food Facts.", 404) from e
        raise
    if data.get("status") != 1 or not data.get("product"):
        raise OFFError("not_found", "No product with this barcode in Open Food Facts.", 404)
    return normalize_product(data["product"], barcode)


def _search_sal(q: str, page: int) -> dict:
    """Search-a-licious (documented text-search service). Isolated so it is easy to swap."""
    params = {"q": q, "page": page, "page_size": PAGE_SIZE, "fields": SEARCH_FIELDS}
    data = _get_json(f"{OFF_SEARCH_URL}?{urllib.parse.urlencode(params)}")
    # Search-a-licious has used "hits"; the classic API uses "products". Accept both.
    return {"items": data.get("hits") or data.get("products") or [], "total": data.get("count")}


def _search_legacy(q: str, page: int) -> dict:
    """Older /cgi/search.pl endpoint, used only if Search-a-licious fails."""
    params = {"search_terms": q, "search_simple": 1, "action": "process", "json": 1,
              "page": page, "page_size": PAGE_SIZE, "fields": SEARCH_FIELDS}
    data = _get_json(f"{OFF_BASE_URL}/cgi/search.pl?{urllib.parse.urlencode(params)}")
    return {"items": data.get("products") or [], "total": data.get("count")}


def search_products(query: str, page: int = 1) -> SearchResponse:
    q = (query or "").strip()
    if len(q) < 2 or len(q) > 100:
        raise OFFError("invalid_query", "Search text must be 2 to 100 characters.", 422)
    page = max(1, min(int(page), 50))
    try:
        found = _search_sal(q, page)
    except OFFError:
        found = _search_legacy(q, page)  # if this fails too, its error is raised
    hits = [h for h in (_to_hit(item) for item in found["items"]) if h]
    total = _number(found["total"])
    return SearchResponse(query=q, page=page, page_size=PAGE_SIZE,
                          total=int(total) if total is not None else None, results=hits)
