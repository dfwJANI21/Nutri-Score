"""Nutri-Score engine (updated 2023 algorithm) for GENERAL FOODS.

Not supported (they return "Score unavailable"): beverages, fats/oils/nuts/seeds, cheese,
meat. They have their own official rules, and guessing would give misleading grades.
All numbers live in rules_2023.py.
"""
from models import Product
import rules_2023 as rules

ALGORITHM_VERSION = "Nutri-Score 2023 update (general foods)"


class ScoreUnavailable(Exception):
    """A reliable grade cannot be calculated. The message is shown to the user."""


def points(value: float, thresholds: list) -> int:
    """One point for every threshold the value is strictly above."""
    return sum(1 for t in thresholds if value > t)


def fvl_points(percent: float) -> int:
    earned = 0
    for limit, pts in rules.FRUIT_VEG_LEGUMES_PCT:
        if percent > limit:
            earned = pts
    return earned


def choose_category(product: Product) -> str:
    tags = product.categories_tags
    if not tags:
        raise ScoreUnavailable("The product category is unknown, so the right rules cannot be chosen.")
    for name, wanted in rules.UNSUPPORTED_CATEGORIES.items():
        if any(t in wanted for t in tags):
            raise ScoreUnavailable(f"This looks like {name}, which has its own Nutri-Score rules "
                                   "that this project does not implement yet.")
    return "general foods"


def grade_for(score: int) -> str:
    for highest, grade in rules.GRADE_BOUNDARIES:
        if score <= highest:
            return grade
    return "E"


def calculate_nutriscore(product: Product) -> dict:
    category = choose_category(product)
    n = product.nutrition

    energy_kj, converted = n.energy_kj, False
    if energy_kj is None and n.energy_kcal is not None:
        energy_kj, converted = n.energy_kcal * 4.184, True   # official tables use kJ

    needed = {"energy": energy_kj, "sugars": n.sugars_g, "saturated fat": n.saturated_fat_g,
              "salt": n.salt_g, "fibre": n.fiber_g, "protein": n.proteins_g,
              "fruit, vegetable and legume content": n.fruits_veg_legumes_pct}
    missing = [name for name, value in needed.items() if value is None]
    if missing:
        raise ScoreUnavailable("Missing from the source data: " + ", ".join(missing) + ".")

    negative = {
        "energy": points(energy_kj, rules.ENERGY_KJ),
        "sugars": points(n.sugars_g, rules.SUGARS_G),
        "saturated fat": points(n.saturated_fat_g, rules.SATURATED_FAT_G),
        "salt": points(n.salt_g, rules.SALT_G),
    }
    positive = {
        "fibre": points(n.fiber_g, rules.FIBRE_G),
        "fruit, vegetables and legumes": fvl_points(n.fruits_veg_legumes_pct),
    }
    protein_pts = points(n.proteins_g, rules.PROTEIN_G)

    N = sum(negative.values())
    protein_counted = N < rules.PROTEIN_CAP_N
    if protein_counted:
        positive["protein"] = protein_pts
    P = sum(positive.values())
    score = N - P

    return {
        "grade": grade_for(score),
        "category": category,
        "details": {
            "negative_points": negative, "positive_points": positive,
            "N": N, "P": P, "score": score,
            "protein_counted": protein_counted,
            "energy_converted_from_kcal": converted,
        },
    }
