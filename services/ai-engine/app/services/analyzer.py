from app.models.schemas import AnalysisReport, AnalyzeLinkPayload, ResearchPreferences
from app.services.marketplace_comparison import build_marketplace_comparison
from app.services.llm_summary import build_analysis_report
from app.services.price_intelligence import build_pricing_insight
from app.services.product_parser import fetch_product_page, parse_product_identity
from app.services.review_sources import gather_review_signals


def _default_preferences() -> ResearchPreferences:
    return ResearchPreferences(
        compareAcrossMarketplaces=True,
        selectedMarketplaces=[
            "amazon",
            "flipkart",
            "ajio",
            "myntra",
            "nykaa",
            "tatacliq",
            "meesho",
            "croma",
            "reliance-digital",
            "vijay-sales",
            "snapdeal",
            "jiomart",
            "firstcry",
            "hm",
            "zara",
            "best-buy",
        ],
        includeReddit=True,
        includeYouTube=True,
        includeEditorial=True,
        dealPreference="balanced",
        showPriceDeltaPercent=True,
    )


async def analyze_product_link(payload: AnalyzeLinkPayload) -> AnalysisReport:
    url = str(payload.url)
    preferences = payload.preferences or _default_preferences()
    product_page_html = await fetch_product_page(url)
    product = parse_product_identity(url, html=product_page_html)
    pricing = build_pricing_insight(
        url,
        product,
        html=product_page_html,
        deal_preference=preferences.deal_preference,
        marketplace_prices=[],
    )
    pricing.marketplace_prices = await build_marketplace_comparison(
        product_url=url,
        product=product,
        pricing=pricing,
        preferences=preferences,
    )
    sources = await gather_review_signals(product, product_url=url, preferences=preferences)
    return await build_analysis_report(url, product, pricing, sources)
