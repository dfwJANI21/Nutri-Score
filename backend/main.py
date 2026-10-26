"""FastAPI app: a few small routes + serves the frontend folder.

Run from the backend folder:  uvicorn main:app --reload
Then open http://localhost:8000
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

import off_client
import scoring
from models import AnalysisResponse, CalculatedScore, Product, SearchResponse
from off_client import OFFError

app = FastAPI(title="NutriScore (student project)")


@app.exception_handler(OFFError)
async def off_error_handler(request, exc: OFFError):
    """Every data-source problem becomes {"error": {"code": ..., "message": ...}}."""
    return JSONResponse(status_code=exc.status, content={"error": {"code": exc.code, "message": exc.message}})


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/search", response_model=SearchResponse)
def search(q: str = "", page: int = 1):
    return off_client.search_products(q, page)


@app.get("/api/product/{barcode}", response_model=Product)
def product(barcode: str):
    return off_client.get_product(barcode)


@app.get("/api/analysis/{barcode}", response_model=AnalysisResponse)
def analysis(barcode: str):
    product = off_client.get_product(barcode)

    # Hand the product to the scoring engine. If it cannot give a reliable grade, say so.
    try:
        result = scoring.calculate_nutriscore(product)
        calculated = CalculatedScore(status="calculated", grade=result["grade"],
                                     algorithm=scoring.ALGORITHM_VERSION, details=result.get("details"))
    except scoring.ScoreUnavailable as e:
        calculated = CalculatedScore(status="unavailable", algorithm=scoring.ALGORITHM_VERSION, reason=str(e))
    except NotImplementedError:
        calculated = CalculatedScore(status="unavailable", algorithm=scoring.ALGORITHM_VERSION,
                                     reason="Scoring engine not implemented yet.")

    return AnalysisResponse(product=product, source_grade=product.off_nutriscore_grade, calculated=calculated)


# Must stay LAST so it does not swallow the /api routes
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
