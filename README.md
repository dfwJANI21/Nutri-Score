# NutriScore

A small food-nutrition explorer. Search a product by name or barcode, see its real nutrition data
from Open Food Facts, and a Nutri-Score grade calculated by this project's own code.

Plain HTML/CSS/JavaScript frontend + a small FastAPI backend. Only one external service is used:
[Open Food Facts](https://openfoodfacts.github.io/documentation/) (data only; it never decides our grade).

## Run it
Needs Python 3.9+.
```
pip install -r requirements.txt
cd backend
python -m uvicorn main:app --reload
```
Open http://localhost:8000. API docs: http://localhost:8000/docs

Before real use, put your own email in `USER_AGENT` in `backend/off_client.py`
(Open Food Facts asks apps to identify themselves).

Tests (from the project root): `python -m pytest -q`

## Barcode scanning
On the home page you can find a product three ways: search by name, scan its barcode with the
camera, or scan a photo of the barcode. You can also type the number under the barcode.
- Scanning is done in the browser by the open-source `html5-qrcode` library (bundled in `frontend/js/lib/`).
  Camera images are not uploaded anywhere.
- The camera needs `http://localhost:8000` or https. It will not work from an address like `http://192.168.x.x:8000`.
- Supported barcodes: EAN-13, EAN-8, UPC-A, UPC-E (what you find on food packs).

## How the grade is calculated
Updated 2023 Nutri-Score algorithm for **general foods**, per 100 g:
- Unfavourable points N: energy (0-10), sugars (0-15), saturated fat (0-10), salt (0-20)
- Favourable points P: fibre (0-5), fruit/vegetables/legumes (0-5), protein (0-7, only counted if N < 11)
- Score = N - P. Grades: A <= -1, B 0 to 2, C 3 to 10, D 11 to 18, E >= 19
- All tables are in `backend/rules_2023.py` with their sources; the logic is in `backend/scoring.py`.

**Not supported -> "Score unavailable":** beverages, fats/oils/nuts/seeds, cheese, meat (they have their
own official rules), products with an unknown category, and any product with a missing required value.
Missing values are never replaced by 0.

## Things to verify on real data (the live Open Food Facts API could not be reached while building this)
1. Look up a few real barcodes and compare "Calculated" with "Listed by Open Food Facts". Small
   differences are possible; big ones are worth investigating.
2. The fruit/vegetable/legume percentage is read from `fruits-vegetables-legumes_100g`, then
   `fruits-vegetables-legumes-estimate-from-ingredients_100g` (see `FVL_KEYS` in `off_client.py`).
   If real products always show it as missing, check the field name in the Open Food Facts API response.
3. Name search uses Search-a-licious (documented by Open Food Facts, still beta), with the older
   `/cgi/search.pl` as a fallback. If search returns nothing, check `_search_sal()` against the current docs.

## Files
| File | Purpose |
|---|---|
| `backend/off_client.py` | Open Food Facts calls, error handling, normalizing |
| `backend/models.py` | Data shapes (Pydantic) |
| `backend/rules_2023.py` | Official point tables and grade boundaries |
| `backend/scoring.py` | Scoring engine |
| `backend/main.py` | API routes + serves the frontend |
| `frontend/index.html`, `product.html`, `about.html` | The three pages (search + scanner, product analysis, method) |
| `frontend/css/style.css` | All styling (blue, pink and yellow design) |
| `frontend/js/api.js` | Talks to the backend |
| `frontend/js/search.js` | Search by name, results and paging |
| `frontend/js/scanner.js` | Camera, photo and typed barcode lookup |
| `frontend/js/product.js` | Fills the product page |
| `frontend/js/lib/` | Bundled `html5-qrcode` scanner library (Apache-2.0) |
| `tests/` | Client, API and scoring tests |

## API contract (shapes only; `null` means the source did not provide it)
`GET /api/search?q=text&page=1`
```
{ "query": str, "page": int, "page_size": int, "total": int|null,
  "results": [ { "barcode": str, "name": str|null, "brand": str|null, "category": str|null,
                 "image_url": str|null, "off_nutriscore_grade": "a".."e"|null } ] }
```
`GET /api/product/{barcode}`
```
{ "barcode": str, "name": str|null, "brand": str|null, "category": str|null, "categories_tags": [str],
  "image_url": str|null, "ingredients_text": str|null, "quantity": str|null,
  "nutrition": { "energy_kcal", "energy_kj", "fat_g", "saturated_fat_g", "carbohydrates_g", "sugars_g",
                 "fiber_g", "proteins_g", "salt_g", "fruits_veg_legumes_pct": each number|null },
  "off_nutriscore_grade": "a".."e"|null, "missing_nutrients": [str], "source": str, "source_url": str }
```
`GET /api/analysis/{barcode}`
```
{ "product": <product above>,
  "source_grade": "a".."e"|null,                      // from Open Food Facts, NOT ours
  "calculated": { "status": "calculated"|"unavailable", "grade": "A".."E"|null,
                  "algorithm": str, "reason": str|null,
                  "details": { "negative_points": {...}, "positive_points": {...}, "N": int, "P": int,
                               "score": int, "protein_counted": bool, ... }|null } }
```
Errors (any route): `{ "error": { "code": str, "message": str } }` with codes
`invalid_barcode`, `invalid_query`, `not_found`, `unreachable`, `http_error`, `bad_response`.

## References
- Open Food Facts documentation: https://openfoodfacts.github.io/documentation/
- Official Nutri-Score information: https://www.santepubliquefrance.fr/en/nutri-score
- Scientific committee update report: https://www.blv.admin.ch/dam/fr/sd-web/gIxXfypDnYOO/aktuelisierungsbericht-gremiums-nutri-score-2022-en.pdf
- Q&A on the updated algorithm: https://www.santepubliquefrance.fr/sites/default/files/rdd/document/FAQ-updatedAlgo-V11.pdf
- Scientific discussion of the 2023 update: https://www.nature.com/articles/s43016-024-00920-3

## Attribution
Barcode scanning: [html5-qrcode](https://github.com/mebjas/html5-qrcode) by Minhaz (mebjas), Apache-2.0, included unchanged.
Product data: Open Food Facts contributors, ODbL 1.0. NutriScore is an independent educational
project, not an official Nutri-Score service and not endorsed by its owners.
