"""Nutri-Score 2023 rule tables for GENERAL FOODS, per 100 g.

A value earns one point for every threshold it is strictly GREATER than
(so a value exactly equal to a threshold does not earn that point).

Sources:
 - Nutri-Score scientific committee, "Update of the Nutri-Score algorithm" (2022 report)
   https://www.blv.admin.ch/dam/fr/sd-web/gIxXfypDnYOO/aktuelisierungsbericht-gremiums-nutri-score-2022-en.pdf
 - Santé publique France, Q&A on the updated algorithm
   https://www.santepubliquefrance.fr/sites/default/files/rdd/document/FAQ-updatedAlgo-V11.pdf
 - Nature Food, 2024: https://www.nature.com/articles/s43016-024-00920-3
"""

# ---- unfavourable components (N points) ----
ENERGY_KJ = [335, 670, 1005, 1340, 1675, 2010, 2345, 2680, 3015, 3350]            # max 10
SUGARS_G = [3.4, 6.8, 10, 14, 17, 20, 24, 27, 31, 34, 37, 41, 44, 48, 51]         # max 15
SATURATED_FAT_G = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]                                 # max 10
SALT_G = [round(0.2 * k, 1) for k in range(1, 21)]                                # max 20

# ---- favourable components (P points) ----
PROTEIN_G = [2.4, 4.8, 7.2, 9.6, 12, 14, 17]                                      # max 7
FIBRE_G = [3.0, 4.1, 5.2, 6.3, 7.4]                                               # max 5
FRUIT_VEG_LEGUMES_PCT = [(40, 1), (60, 2), (80, 5)]   # (strictly more than %, points)   max 5

# Protein only counts when N < 11 (general foods)
PROTEIN_CAP_N = 11

# Score -> grade: (highest score that still gets this grade, grade)
GRADE_BOUNDARIES = [(-1, "A"), (2, "B"), (10, "C"), (18, "D")]   # anything above 18 is "E"

# Categories (Open Food Facts category tags) that have their OWN rules in the official
# algorithm. We do not implement those, so they get "Score unavailable" (never a guess).
UNSUPPORTED_CATEGORIES = {
    "beverages": ["en:beverages", "en:waters", "en:milks", "en:dairy-drinks"],
    "fats, oils, nuts or seeds": ["en:fats", "en:oils", "en:vegetable-oils", "en:animal-fats",
                                  "en:butters", "en:margarines", "en:nuts", "en:seeds"],
    "cheese": ["en:cheeses"],
    "meat": ["en:meats"],
}
