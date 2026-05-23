from app.models.schemas import AnalysisReport, AnalyzeLinkPayload
from app.services.llm_summary import build_analysis_report
from app.services.price_intelligence import build_pricing_insight
from app.services.product_parser import fetch_product_page, parse_product_identity
from app.services.review_sources import gather_review_signals


async def analyze_product_link(payload: AnalyzeLinkPayload) -> AnalysisReport:
    url = str(payload.url)
    product_page_html = await fetch_product_page(url)
    product = parse_product_identity(url, html=product_page_html)
    pricing = build_pricing_insight(url, product, html=product_page_html)
    sources = await gather_review_signals(product, product_url=url)
    return await build_analysis_report(url, product, pricing, sources)
