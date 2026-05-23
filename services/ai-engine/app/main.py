from fastapi import FastAPI

from app.models.schemas import AnalysisReport, AnalyzeLinkPayload
from app.services.adapters.registry import SUPPORTED_MARKETPLACES
from app.services.analyzer import analyze_product_link

app = FastAPI(
    title="Scout AI Engine",
    version="0.1.0",
    description="Product analysis service for multi-marketplace shopping research.",
)


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "supportedMarketplaces": [adapter.label for adapter in SUPPORTED_MARKETPLACES],
    }


@app.post("/analyze", response_model=AnalysisReport)
async def analyze(payload: AnalyzeLinkPayload) -> AnalysisReport:
    return await analyze_product_link(payload)
