from app.models.schemas import AnalysisReport, AnalyzeLinkPayload
from app.services.llm_summary import build_analysis_report
from app.services.price_intelligence import build_pricing_insight
from app.services.product_parser import parse_product_identity
from app.services.review_sources import gather_review_signals


async def analyze_product_link(payload: AnalyzeLinkPayload) -> AnalysisReport:
    product = parse_product_identity(str(payload.url))
    pricing = build_pricing_insight(str(payload.url))
    sources = gather_review_signals(product)
    return await build_analysis_report(str(payload.url), product, pricing, sources)
