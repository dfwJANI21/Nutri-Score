"""Scoring tests. Expected values come from the official 2023 tables (see rules_2023.py)
and hand calculation, not from this project's own output."""
import pytest

import scoring
from models import Nutrition, Product
from scoring import ScoreUnavailable, calculate_nutriscore, grade_for, points


def make(tags=("en:snacks",), **nutrition):
    base = dict(energy_kj=0, sugars_g=0, saturated_fat_g=0, salt_g=0,
                fiber_g=0, proteins_g=0, fruits_veg_legumes_pct=0)
    base.update(nutrition)
    return Product(barcode="12345678", categories_tags=list(tags),
                   nutrition=Nutrition(**base), source_url="x")


# ---- threshold rule: strictly greater than ----
def test_value_equal_to_threshold_does_not_earn_the_point():
    assert points(3.4, scoring.rules.SUGARS_G) == 0
    assert points(3.41, scoring.rules.SUGARS_G) == 1


def test_maximum_points_per_component():
    assert points(52, scoring.rules.SUGARS_G) == 15
    assert points(4.1, scoring.rules.SALT_G) == 20
    assert points(3351, scoring.rules.ENERGY_KJ) == 10
    assert points(11, scoring.rules.SATURATED_FAT_G) == 10
    assert points(18, scoring.rules.PROTEIN_G) == 7
    assert points(7.5, scoring.rules.FIBRE_G) == 5


def test_fruit_veg_legume_points():
    assert [scoring.fvl_points(x) for x in (40, 41, 60, 61, 80, 81)] == [0, 1, 1, 2, 2, 5]


# ---- grade boundaries (general foods) ----
@pytest.mark.parametrize("score,grade", [(-15, "A"), (-1, "A"), (0, "B"), (2, "B"), (3, "C"),
                                         (10, "C"), (11, "D"), (18, "D"), (19, "E"), (40, "E")])
def test_grade_boundaries(score, grade):
    assert grade_for(score) == grade


# ---- full calculations done by hand ----
def test_very_healthy_product_is_A():
    # N = 0; P = fibre 5 + fruit/veg 5 = 10 (protein 0) -> score -10 -> A
    r = calculate_nutriscore(make(fiber_g=8, fruits_veg_legumes_pct=90))
    assert (r["details"]["N"], r["details"]["P"], r["details"]["score"], r["grade"]) == (0, 10, -10, "A")


def test_worst_case_is_E():
    # N = 10 + 15 + 10 + 20 = 55, protein not counted (N >= 11), no fibre/fruit -> 55 -> E
    r = calculate_nutriscore(make(energy_kj=3400, sugars_g=52, saturated_fat_g=11, salt_g=4.1, proteins_g=20))
    assert r["details"]["N"] == 55 and r["details"]["score"] == 55 and r["grade"] == "E"
    assert r["details"]["protein_counted"] is False


def test_protein_counts_when_N_is_below_11():
    # N = energy 336 kJ -> 1 point; protein 18 g -> 7 points; score = 1 - 7 = -6 -> A
    r = calculate_nutriscore(make(energy_kj=336, proteins_g=18))
    assert r["details"]["protein_counted"] is True
    assert r["details"]["score"] == -6 and r["grade"] == "A"


def test_energy_is_converted_from_kcal_only_when_kj_missing():
    p = make(energy_kj=None, energy_kcal=100)
    r = calculate_nutriscore(p)
    assert r["details"]["energy_converted_from_kcal"] is True
    assert r["details"]["negative_points"]["energy"] == 1   # 100 kcal = 418.4 kJ > 335


# ---- "Score unavailable" cases ----
def test_missing_nutrient_is_unavailable_not_zero():
    with pytest.raises(ScoreUnavailable, match="fibre"):
        calculate_nutriscore(make(fiber_g=None))


def test_missing_fruit_veg_legumes_is_unavailable():
    with pytest.raises(ScoreUnavailable, match="fruit"):
        calculate_nutriscore(make(fruits_veg_legumes_pct=None))


def test_unknown_category_is_unavailable():
    with pytest.raises(ScoreUnavailable, match="category is unknown"):
        calculate_nutriscore(make(tags=()))


@pytest.mark.parametrize("tag", ["en:beverages", "en:cheeses", "en:vegetable-oils", "en:meats"])
def test_categories_with_their_own_rules_are_unavailable(tag):
    with pytest.raises(ScoreUnavailable, match="own Nutri-Score rules"):
        calculate_nutriscore(make(tags=("en:snacks", tag)))
