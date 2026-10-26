"""Data shapes used by the API (Pydantic validates and documents them).

AI-assisted file. Every nutrition field is Optional on purpose: Open Food Facts is
crowd-sourced, so a missing value means "nobody entered it", NOT zero.
"""
from typing import List, Optional

from pydantic import BaseModel


class Nutrition(BaseModel):
    """Values per 100 g (or 100 ml for drinks). None = not provided by the source."""
    energy_kcal: Optional[float] = None
    energy_kj: Optional[float] = None
    fat_g: Optional[float] = None
    saturated_fat_g: Optional[float] = None
    carbohydrates_g: Optional[float] = None
    sugars_g: Optional[float] = None
    fiber_g: Optional[float] = None
    proteins_g: Optional[float] = None
    salt_g: Optional[float] = None
    fruits_veg_legumes_pct: Optional[float] = None  # % of fruit, vegetables and legumes


class Product(BaseModel):
    barcode: str
    name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    categories_tags: List[str] = []              # e.g. "en:snacks" (used to pick the scoring rules)
    image_url: Optional[str] = None
    ingredients_text: Optional[str] = None
    quantity: Optional[str] = None
    nutrition: Nutrition
    off_nutriscore_grade: Optional[str] = None  # grade stored by Open Food Facts (NOT ours)
    missing_nutrients: List[str] = []           # key nutrients the source did not provide
    source: str = "Open Food Facts"
    source_url: str


class SearchHit(BaseModel):
    barcode: str
    name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    off_nutriscore_grade: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    page: int
    page_size: int
    total: Optional[int] = None
    results: List[SearchHit]


class CalculatedScore(BaseModel):
    """Result of OUR scoring engine (scoring.py)."""
    status: str                       # "calculated" or "unavailable"
    grade: Optional[str] = None       # "A".."E" only when status == "calculated"
    algorithm: str
    reason: Optional[str] = None      # why it is unavailable
    details: Optional[dict] = None    # points breakdown, if you return one


class AnalysisResponse(BaseModel):
    product: Product
    source_grade: Optional[str] = None   # from Open Food Facts - never presented as ours
    calculated: CalculatedScore
