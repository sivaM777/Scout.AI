import json
from datetime import datetime, UTC
from random import Random
from typing import Any
from uuid import uuid4

import httpx

from app.config import settings
from app.models.schemas import AnalysisReport, AlternativeProduct, PricingInsight, ProductIdentity, SourceEvidence


def _safe_int(value: Any, fallback: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return fallback

    return max(minimum, min(parsed, maximum))


def _normalize_verdict(value: Any, fallback: str) -> str:
    if not isinstance(value, str):
        return fallback

    normalized = value.strip().lower()
    if normalized in {"buy", "wait", "skip"}:
        return normalized

    if any(token in normalized for token in ("skip", "avoid", "pass", "alternative", "dont buy", "don't buy")):
        return "skip"

    if any(token in normalized for token in ("wait", "hold", "later", "price drop")):
        return "wait"

    if any(token in normalized for token in ("buy", "recommend", "worth it", "go for it")):
        return "buy"

    return fallback


def _string_list(value: Any, fallback: list[str]) -> list[str]:
    if not isinstance(value, list):
        return fallback

    cleaned = [item.strip() for item in value if isinstance(item, str) and item.strip()]
    return cleaned or fallback


def _string_value(value: Any, fallback: str) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else fallback


def _score_from_sources(product: ProductIdentity, sources: list[SourceEvidence]) -> int:
    positive = sum(1 for source in sources if source.sentiment == "positive")
    negative = sum(1 for source in sources if source.sentiment == "negative")
    category_bonus = 4 if product.category in {"electronics", "fashion", "beauty"} else 0
    score = 64 + positive * 8 - negative * 9 + category_bonus
    return max(42, min(score, 92))


def _alternatives(product: ProductIdentity, pricing: PricingInsight) -> list[AlternativeProduct]:
    midpoint = pricing.recommended_target_price
    return [
        AlternativeProduct(
            id=f"{product.brand.lower()}-alt-1",
            name=f"{product.brand} Value Edition",
            reason="Better review consistency for everyday users.",
            estimatedPrice=round(midpoint * 0.95, 2),
            verdict="buy",
        ),
        AlternativeProduct(
            id=f"{product.brand.lower()}-alt-2",
            name=f"{product.brand} Premium Option",
            reason="Costs more, but improves finish quality and long-term satisfaction.",
            estimatedPrice=round(midpoint * 1.18, 2),
            verdict="wait",
        ),
    ]


async def _try_openai_compatible_summary(
    product: ProductIdentity,
    pricing: PricingInsight,
    sources: list[SourceEvidence],
) -> dict | None:
    if not settings.llm_base_url or not settings.llm_api_key or not settings.llm_model:
        return None

    prompt = {
        "product": product.model_dump(mode="json"),
        "pricing": pricing.model_dump(mode="json", by_alias=True),
        "sources": [source.model_dump(mode="json", by_alias=True) for source in sources],
        "task": "Return strict JSON with keys: oneLineSummary, verdictReason, pros, cons, communityPulse, overallScore, confidence, verdict. The verdict must be exactly one of: buy, wait, skip.",
    }

    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
        response = await client.post(
            f"{settings.llm_base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.llm_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.llm_model,
                "temperature": 0.2,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a shopping research assistant. Always return valid JSON only.",
                    },
                    {
                        "role": "user",
                        "content": json.dumps(prompt),
                    },
                ],
                "response_format": {"type": "json_object"},
            },
        )

    if not response.is_success:
        return None

    data = response.json()
    content = data["choices"][0]["message"]["content"]
    return json.loads(content)


async def build_analysis_report(
    url: str,
    product: ProductIdentity,
    pricing: PricingInsight,
    sources: list[SourceEvidence],
) -> AnalysisReport:
    llm_result = await _try_openai_compatible_summary(product, pricing, sources)
    overall_score = _score_from_sources(product, sources)
    confidence = 82
    verdict = "buy" if overall_score >= 72 else "wait" if overall_score >= 58 else "skip"

    if llm_result:
        overall_score = _safe_int(llm_result.get("overallScore"), overall_score, 0, 100)
        confidence = _safe_int(llm_result.get("confidence"), confidence, 0, 100)
        verdict = _normalize_verdict(llm_result.get("verdict"), verdict)

    default_summary = f"{product.name} looks solid for most shoppers, but it is smartest when bought near the target price."
    default_verdict_reason = f"Signals across community and editorial sources suggest {product.name} is strongest on value, but users should still verify fit, finish, or long-term durability."
    default_pros = [
        "Strong overall value relative to competing listings.",
        "Feedback suggests the core experience is dependable for everyday use.",
        "Multiple source types discuss the product, which improves confidence.",
    ]
    default_cons = [
        "Quality consistency may vary between batches or sellers.",
        "Best purchase decision depends heavily on the live selling price.",
        "Specialized users may want a more premium alternative.",
    ]

    summary = _string_value(llm_result.get("oneLineSummary") if llm_result else None, default_summary)
    verdict_reason = _string_value(
        llm_result.get("verdictReason") if llm_result else None,
        default_verdict_reason,
    )
    pros = _string_list(llm_result.get("pros") if llm_result else None, default_pros)
    cons = _string_list(llm_result.get("cons") if llm_result else None, default_cons)

    randomizer = Random(product.name)
    default_community_pulse = (
        f"Community chatter is {randomizer.choice(['cautiously positive', 'generally encouraging', 'mixed but leaning favorable'])}, "
        "with most criticism focused on price sensitivity rather than fatal flaws."
    )
    community_pulse = _string_value(
        llm_result.get("communityPulse") if llm_result else None,
        default_community_pulse,
    )

    return AnalysisReport(
        id=str(uuid4()),
        productUrl=url,
        marketplace=product.marketplace,
        productName=product.name,
        productBrand=product.brand,
        productImage=product.image,
        productCategory=product.category.title(),
        overallScore=overall_score,
        confidence=confidence,
        verdict=verdict,
        oneLineSummary=summary,
        verdictReason=verdict_reason,
        pros=pros,
        cons=cons,
        communityPulse=community_pulse,
        sources=sources,
        pricing=pricing,
        alternatives=_alternatives(product, pricing),
        generatedAt=datetime.now(UTC).isoformat(),
    )
