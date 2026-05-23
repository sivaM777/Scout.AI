from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import settings
from app.models.schemas import MarketplacePrice, PricingInsight, ProductIdentity, ResearchPreferences
from app.services.adapters.registry import MarketplaceAdapter, resolve_marketplace, resolve_marketplace_slug
from app.services.price_intelligence import build_pricing_insight
from app.services.product_parser import PRODUCT_PAGE_HEADERS, parse_product_identity


SEARCH_HEADERS = {
    **PRODUCT_PAGE_HEADERS,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
NAME_STOPWORDS = {
    "and",
    "buy",
    "edition",
    "for",
    "from",
    "pack",
    "piece",
    "product",
    "review",
    "sale",
    "with",
}


@dataclass(frozen=True)
class ComparisonCandidate:
    adapter: MarketplaceAdapter
    product: ProductIdentity
    pricing: PricingInsight
    url: str
    match_score: float


def _search_phrase(product: ProductIdentity) -> str:
    phrase = product.name.strip()
    if not phrase.lower().startswith(product.brand.lower()):
        phrase = f"{product.brand} {phrase}"
    return " ".join(token for token in phrase.split() if token)


def _tokenize_name(value: str) -> set[str]:
    tokens = set()
    for raw in value.lower().replace("-", " ").replace("/", " ").split():
        token = "".join(char for char in raw if char.isalnum())
        if len(token) < 2 or token in NAME_STOPWORDS:
            continue
        tokens.add(token)
    return tokens


def _name_similarity(target: ProductIdentity, candidate: ProductIdentity) -> float:
    target_tokens = _tokenize_name(f"{target.brand} {target.name}")
    candidate_tokens = _tokenize_name(f"{candidate.brand} {candidate.name}")
    if not target_tokens or not candidate_tokens:
        return 0.0

    overlap = len(target_tokens & candidate_tokens)
    union = len(target_tokens | candidate_tokens)
    jaccard = overlap / union if union else 0.0

    brand_bonus = 0.18 if target.brand.lower() == candidate.brand.lower() else 0.0
    category_bonus = 0.08 if target.category == candidate.category else 0.0
    return min(jaccard + brand_bonus + category_bonus, 1.0)


def _unwrap_duckduckgo_href(raw_href: str) -> str | None:
    if not raw_href:
        return None

    if raw_href.startswith("//duckduckgo.com/l/?"):
        raw_href = f"https:{raw_href}"

    if raw_href.startswith("https://duckduckgo.com/l/?") or raw_href.startswith("http://duckduckgo.com/l/?"):
        query = parse_qs(urlparse(raw_href).query)
        target = query.get("uddg", [None])[0]
        return unquote(target) if target else None

    if raw_href.startswith("http://") or raw_href.startswith("https://"):
        return raw_href

    return None


def _extract_marketplace_urls(html: str, adapter: MarketplaceAdapter) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    urls: list[str] = []
    seen: set[str] = set()

    for link in soup.find_all("a", href=True):
        resolved = _unwrap_duckduckgo_href(link["href"])
        if not resolved:
            continue

        hostname = (urlparse(resolved).hostname or "").lower()
        if not any(hostname.endswith(domain) for domain in adapter.domains):
            continue

        normalized = resolved.split("#", maxsplit=1)[0]
        if normalized in seen:
            continue

        seen.add(normalized)
        urls.append(normalized)
        if len(urls) >= 4:
            break

    return urls


async def _search_marketplace_urls(
    client: httpx.AsyncClient,
    adapter: MarketplaceAdapter,
    product: ProductIdentity,
) -> list[str]:
    primary_domain = adapter.domains[0]
    query = f'site:{primary_domain} "{_search_phrase(product)}"'
    response = await client.get(
        "https://html.duckduckgo.com/html/",
        params={"q": query, "kl": "in-en"},
        headers=SEARCH_HEADERS,
    )

    if not response.is_success:
        return []

    return _extract_marketplace_urls(response.text, adapter)


async def _fetch_marketplace_html(client: httpx.AsyncClient, url: str) -> str | None:
    try:
        response = await client.get(url, headers=PRODUCT_PAGE_HEADERS)
    except httpx.HTTPError:
        return None

    if not response.is_success:
        return None

    content_type = response.headers.get("content-type", "")
    if "html" not in content_type.lower():
        return None

    return response.text


def _price_status(current_price: float | None, original_price: float, is_original_listing: bool) -> str:
    if is_original_listing:
        return "current"
    if current_price is None:
        return "unavailable"

    delta = round(current_price - original_price, 2)
    if abs(delta) <= max(original_price * 0.005, 1):
        return "same"
    return "cheaper" if delta < 0 else "higher"


def _unavailable_marketplace_price(
    adapter: MarketplaceAdapter,
    note: str,
    *,
    is_original_listing: bool = False,
) -> MarketplacePrice:
    return MarketplacePrice(
        marketplaceSlug=adapter.slug,
        marketplaceLabel=adapter.label,
        productName=adapter.label,
        productUrl=None,
        currency="INR" if adapter.slug != "best-buy" else "USD",
        currentPrice=None,
        availability="unavailable",
        differenceAmount=None,
        differencePercent=None,
        matchScore=0.0,
        priceStatus="unavailable",
        isOriginalListing=is_original_listing,
        note=note,
    )


def _to_marketplace_price(
    adapter: MarketplaceAdapter,
    candidate: ComparisonCandidate,
    original_price: float,
    *,
    is_original_listing: bool = False,
    note: str | None = None,
) -> MarketplacePrice:
    current_price = round(candidate.pricing.current_price, 2)
    difference_amount = None if is_original_listing else round(current_price - original_price, 2)
    difference_percent = None
    if difference_amount is not None and original_price > 0:
        difference_percent = round((difference_amount / original_price) * 100, 2)

    return MarketplacePrice(
        marketplaceSlug=adapter.slug,
        marketplaceLabel=adapter.label,
        productName=candidate.product.name,
        productUrl=candidate.url,
        currency=candidate.pricing.currency,
        currentPrice=current_price,
        availability="available",
        differenceAmount=difference_amount,
        differencePercent=difference_percent,
        matchScore=round(candidate.match_score, 3),
        priceStatus=_price_status(current_price, original_price, is_original_listing),
        isOriginalListing=is_original_listing,
        note=note if note is not None else (None if is_original_listing else "Matched via live marketplace lookup."),
    )


async def _best_marketplace_candidate(
    client: httpx.AsyncClient,
    adapter: MarketplaceAdapter,
    target_product: ProductIdentity,
    original_price: float,
) -> ComparisonCandidate | None:
    urls = await _search_marketplace_urls(client, adapter, target_product)
    if not urls:
        return None

    best_candidate: ComparisonCandidate | None = None

    for url in urls:
        html = await _fetch_marketplace_html(client, url)
        if not html:
            continue

        candidate_product = parse_product_identity(url, html=html)
        match_score = _name_similarity(target_product, candidate_product)
        if match_score < 0.38:
            continue

        candidate_pricing = build_pricing_insight(
            url,
            candidate_product,
            html=html,
            deal_preference="balanced",
            marketplace_prices=[],
        )

        if candidate_pricing.price_source != "live" or candidate_pricing.current_price <= 0:
            continue

        candidate = ComparisonCandidate(
            adapter=adapter,
            product=candidate_product,
            pricing=candidate_pricing,
            url=url,
            match_score=match_score,
        )

        if best_candidate is None:
            best_candidate = candidate
            continue

        if candidate.match_score > best_candidate.match_score + 0.08:
            best_candidate = candidate
            continue

        best_delta = abs(best_candidate.pricing.current_price - original_price)
        candidate_delta = abs(candidate.pricing.current_price - original_price)
        if candidate.match_score >= best_candidate.match_score and candidate_delta < best_delta:
            best_candidate = candidate

    return best_candidate


def _sorted_marketplace_prices(items: list[MarketplacePrice]) -> list[MarketplacePrice]:
    def sort_key(item: MarketplacePrice) -> tuple[int, float, str]:
        if item.is_original_listing:
            return (0, item.current_price or 0, item.marketplace_label)
        if item.availability == "unavailable":
            return (2, 10**9, item.marketplace_label)
        return (1, item.current_price or 10**9, item.marketplace_label)

    return sorted(items, key=sort_key)


async def build_marketplace_comparison(
    *,
    product_url: str,
    product: ProductIdentity,
    pricing: PricingInsight,
    preferences: ResearchPreferences,
) -> list[MarketplacePrice]:
    if not preferences.compare_across_marketplaces:
        return []

    original_adapter = resolve_marketplace(product_url)
    selected_slugs = list(dict.fromkeys(preferences.selected_marketplaces))
    adapters: list[MarketplaceAdapter] = []

    if original_adapter.slug != "generic":
        adapters.append(original_adapter)

    for slug in selected_slugs:
        adapter = resolve_marketplace_slug(slug)
        if adapter and adapter.slug not in {item.slug for item in adapters}:
            adapters.append(adapter)

    original_candidate = ComparisonCandidate(
        adapter=original_adapter,
        product=product,
        pricing=pricing,
        url=product_url,
        match_score=1.0,
    )
    original_price = pricing.current_price
    original_note = {
        "live": "Current listing price was extracted live from the product page.",
        "historical": "Current listing price fell back to the last recorded live snapshot.",
        "estimated": "Current listing price is estimated because no live page price was detected.",
    }.get(pricing.price_source, "Current listing")
    items = [
        _to_marketplace_price(
            original_adapter,
            original_candidate,
            original_price,
            is_original_listing=True,
            note=original_note,
        )
    ]

    remaining_adapters = [adapter for adapter in adapters if adapter.slug != original_adapter.slug]
    if not remaining_adapters:
        return items

    timeout = httpx.Timeout(settings.request_timeout_seconds)
    semaphore = asyncio.Semaphore(4)

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=SEARCH_HEADERS) as client:
        async def compare(adapter: MarketplaceAdapter) -> MarketplacePrice:
            async with semaphore:
                try:
                    candidate = await _best_marketplace_candidate(client, adapter, product, original_price)
                except Exception:
                    candidate = None

                if not candidate:
                    return _unavailable_marketplace_price(adapter, "No close live match found.")

                return _to_marketplace_price(adapter, candidate, original_price)

        items.extend(await asyncio.gather(*(compare(adapter) for adapter in remaining_adapters)))

    return _sorted_marketplace_prices(items)
