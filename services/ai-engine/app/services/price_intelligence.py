from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha1
from typing import Any

from bs4 import BeautifulSoup

from app.models.schemas import MarketplacePrice, PricePoint, PricingInsight, ProductIdentity
from app.services.price_store import PriceSnapshotStore, get_price_snapshot_store


HTML_PRICE_META_KEYS = (
    "product:price:amount",
    "og:price:amount",
    "twitter:data1",
    "price",
)
HTML_CURRENCY_META_KEYS = (
    "product:price:currency",
    "og:price:currency",
    "pricecurrency",
)
SITE_PRICE_SELECTORS: dict[str, tuple[tuple[str, str | None], ...]] = {
    "amazon": (
        ("#corePriceDisplay_desktop_feature_div .a-price .a-offscreen", None),
        ("#corePrice_feature_div .a-price .a-offscreen", None),
        (".apexPriceToPay .a-offscreen", None),
        ("#priceblock_ourprice", None),
        ("#priceblock_dealprice", None),
        ("#price_inside_buybox", None),
    ),
    "flipkart": (
        ("div.Nx9bqj", None),
        ("div._30jeq3", None),
        ("[data-testid='price-final']", None),
    ),
    "ajio": (
        ("span.price", None),
        ("div.prod-sp", None),
        ("div.price", None),
    ),
    "myntra": (
        ("span.pdp-price strong", None),
        ("div.pdp-price-info span", None),
    ),
    "nykaa": (
        ("span[data-testid='price-final']", None),
        ("div[class*='price'] span", None),
    ),
    "tata cliq": (
        ("div[class*='Price']", None),
        ("h3[class*='price']", None),
    ),
    "croma": (
        ("span.amount", None),
        ("div.amount", None),
        ("span[class*='amount']", None),
        ("div[class*='price']", "data-price"),
    ),
    "reliance digital": (
        ("div[class*='price'] span", None),
        ("span[class*='TextWeb__Text']", None),
        ("[data-testid='price']", None),
    ),
    "vijay sales": (
        ("span[class*='price']", None),
        ("div[class*='price']", None),
    ),
    "snapdeal": (
        ("span.payBlkBig", None),
        ("span.pdp-final-price", None),
    ),
    "jiomart": (
        ("span.jm-heading-xxs", None),
        ("div[class*='price'] span", None),
    ),
    "firstcry": (
        ("span[class*='price']", None),
        ("div[class*='price']", None),
    ),
    "hm": (
        ("span[data-price]", "data-price"),
        ("span[class*='Price']", None),
    ),
    "zara": (
        ("span.money-amount__main", None),
        ("span[data-qa-qualifier='price-amount-current']", None),
    ),
    "best buy": (
        ("div.priceView-customer-price span", None),
        ("span[aria-hidden='true']", None),
    ),
}
CATEGORY_BASELINES = {
    "beauty": [349.0, 699.0, 1099.0, 1699.0],
    "electronics": [3999.0, 8999.0, 17999.0, 39999.0],
    "fashion": [799.0, 1499.0, 2499.0, 3999.0],
    "general": [999.0, 1999.0, 4999.0, 9999.0],
    "grocery": [99.0, 199.0, 349.0, 599.0],
    "kids": [499.0, 999.0, 1799.0, 2999.0],
}
CATEGORY_VOLATILITY = {
    "beauty": 0.13,
    "electronics": 0.19,
    "fashion": 0.17,
    "general": 0.14,
    "grocery": 0.08,
    "kids": 0.15,
}
MARKETPLACE_PRICE_BIAS = {
    "ajio": -0.02,
    "amazon": 0.01,
    "best buy": 0.03,
    "croma": 0.02,
    "flipkart": -0.01,
    "hm": -0.03,
    "jiomart": -0.04,
    "meesho": -0.05,
    "myntra": -0.02,
    "nykaa": 0.0,
    "reliance digital": 0.02,
    "snapdeal": -0.03,
    "tata cliq": 0.01,
    "vijay sales": 0.01,
    "zara": 0.04,
}


@dataclass(frozen=True)
class ExtractedPrice:
    amount: float | None = None
    currency: str | None = None


def _seed_from_text(value: str) -> int:
    return int(sha1(value.encode("utf-8")).hexdigest()[:8], 16)


def _default_currency(product: ProductIdentity) -> str:
    return "USD" if product.marketplace.lower() == "best buy" else "INR"


def _normalize_currency(value: str | None, fallback: str) -> str:
    if not value:
        return fallback

    normalized = value.strip().upper().replace("US$", "USD").replace("$", "USD")
    if normalized in {"INR", "RS", "RS.", "\u20b9"}:
        return "INR"
    if normalized == "USD":
        return "USD"
    return fallback


def _parse_price_text(value: str, fallback_currency: str) -> ExtractedPrice:
    cleaned = value.replace("\xa0", " ").strip()
    if not cleaned:
        return ExtractedPrice()

    currency = fallback_currency
    if any(token in cleaned for token in ("\u20b9", "Rs", "rs", "INR")):
        currency = "INR"
    elif any(token in cleaned for token in ("US$", "$", "USD")):
        currency = "USD"

    match = re.search(
        r"(?:(?:\u20b9|Rs\.?|INR|US\$|\$|USD)\s*)?(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d{1,2}))?",
        cleaned,
        flags=re.IGNORECASE,
    )
    if not match:
        return ExtractedPrice(currency=currency)

    whole = match.group(1).replace(",", "")
    decimals = match.group(2) or "0"
    return ExtractedPrice(amount=float(f"{whole}.{decimals}"), currency=currency)


def _extract_offer_nodes(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        nodes: list[dict[str, Any]] = []
        item_type = value.get("@type")
        type_names = item_type if isinstance(item_type, list) else [item_type]
        normalized_types = {str(name).lower() for name in type_names if name}

        if {"offer", "aggregateoffer"} & normalized_types:
            nodes.append(value)

        for child in value.values():
            nodes.extend(_extract_offer_nodes(child))
        return nodes

    if isinstance(value, list):
        nodes: list[dict[str, Any]] = []
        for item in value:
            nodes.extend(_extract_offer_nodes(item))
        return nodes

    return []


def _extract_json_ld_price(soup: BeautifulSoup, fallback_currency: str) -> ExtractedPrice:
    for script in soup.find_all("script", type="application/ld+json"):
        if not script.string:
            continue

        try:
            payload = json.loads(script.string)
        except json.JSONDecodeError:
            continue

        for offer in _extract_offer_nodes(payload):
            raw_amount = offer.get("price") or offer.get("lowPrice") or offer.get("highPrice")
            if raw_amount is None:
                continue

            parsed = _parse_price_text(str(raw_amount), fallback_currency)
            if parsed.amount is None:
                continue

            raw_currency = offer.get("priceCurrency")
            currency = _normalize_currency(str(raw_currency) if raw_currency else parsed.currency, fallback_currency)
            return ExtractedPrice(amount=parsed.amount, currency=currency)

    return ExtractedPrice(currency=fallback_currency)


def _extract_meta_price(soup: BeautifulSoup, fallback_currency: str) -> ExtractedPrice:
    meta_price: str | None = None
    meta_currency: str | None = None

    for tag in soup.find_all("meta"):
        key = (tag.get("property") or tag.get("name") or "").strip().lower()
        content = (tag.get("content") or "").strip()
        if not key or not content:
            continue

        if key in HTML_PRICE_META_KEYS and meta_price is None:
            meta_price = content
        if key in HTML_CURRENCY_META_KEYS and meta_currency is None:
            meta_currency = content

    if not meta_price:
        return ExtractedPrice(currency=fallback_currency)

    parsed = _parse_price_text(meta_price, fallback_currency)
    return ExtractedPrice(
        amount=parsed.amount,
        currency=_normalize_currency(meta_currency or parsed.currency, fallback_currency),
    )


def _extract_selector_price(soup: BeautifulSoup, fallback_currency: str) -> ExtractedPrice:
    selectors = (
        "[itemprop='price']",
        "[data-testid*='price']",
        "[data-price]",
        "[class*='price']",
        "[id*='price']",
    )

    for selector in selectors:
        for node in soup.select(selector):
            candidates = [
                node.get("content"),
                node.get("data-price"),
                node.get("aria-label"),
                node.get_text(" ", strip=True),
            ]
            for candidate in candidates:
                if not candidate or len(candidate) > 80:
                    continue

                parsed = _parse_price_text(candidate, fallback_currency)
                if parsed.amount is not None:
                    return parsed

    return ExtractedPrice(currency=fallback_currency)


def _extract_marketplace_selector_price(soup: BeautifulSoup, marketplace: str, fallback_currency: str) -> ExtractedPrice:
    selectors = SITE_PRICE_SELECTORS.get(marketplace.lower())
    if not selectors:
        return ExtractedPrice(currency=fallback_currency)

    for selector, attribute in selectors:
        for node in soup.select(selector):
            candidates = []
            if attribute:
                candidates.append(node.get(attribute))
            candidates.extend(
                [
                    node.get("content"),
                    node.get("data-price"),
                    node.get("aria-label"),
                    node.get_text(" ", strip=True),
                ]
            )

            for candidate in candidates:
                if not candidate or len(candidate) > 120:
                    continue

                parsed = _parse_price_text(candidate, fallback_currency)
                if parsed.amount is not None:
                    return parsed

    return ExtractedPrice(currency=fallback_currency)


def _extract_price_from_html(html: str | None, fallback_currency: str, marketplace: str) -> ExtractedPrice:
    if not html:
        return ExtractedPrice(currency=fallback_currency)

    soup = BeautifulSoup(html, "html.parser")

    for extractor in (
        lambda current_soup, current_currency: _extract_marketplace_selector_price(
            current_soup,
            marketplace,
            current_currency,
        ),
        _extract_json_ld_price,
        _extract_meta_price,
        _extract_selector_price,
    ):
        extracted = extractor(soup, fallback_currency)
        if extracted.amount is not None:
            return extracted

    return ExtractedPrice(currency=fallback_currency)


def _fallback_current_price(seed: int, category: str, marketplace: str) -> float:
    baselines = CATEGORY_BASELINES.get(category, CATEGORY_BASELINES["general"])
    base_price = baselines[seed % len(baselines)]
    bias = MARKETPLACE_PRICE_BIAS.get(marketplace.lower(), 0.0)
    spread = 90 if category == "grocery" else 450 if category in {"beauty", "fashion", "kids"} else 1600
    current_price = base_price * (1 + bias) + (seed % spread)
    return round(current_price, 2)


def _history_points(current_price: float, seed: int, volatility: float) -> list[PricePoint]:
    drift = ((seed % 9) - 4) / 100
    factors = [
        1.10 + volatility + drift,
        1.06 + (volatility / 2) + (drift / 2),
        1.03 + (drift / 3),
        1.01 - (drift / 4),
        1.0,
    ]
    labels = ["90d", "60d", "30d", "7d", "Now"]
    return [
        PricePoint(label=label, value=round(max(current_price * factor, current_price * 0.72), 2))
        for label, factor in zip(labels, factors, strict=True)
    ]


def build_pricing_insight(
    url: str,
    product: ProductIdentity,
    html: str | None = None,
    snapshot_store: PriceSnapshotStore | None = None,
    observed_at: datetime | None = None,
    deal_preference: str = "balanced",
    marketplace_prices: list[MarketplacePrice] | None = None,
) -> PricingInsight:
    seed = _seed_from_text(f"{url}|{product.marketplace}|{product.name}|{product.brand}")
    fallback_currency = _default_currency(product)
    extracted = _extract_price_from_html(html, fallback_currency, product.marketplace)
    currency = _normalize_currency(extracted.currency, fallback_currency)

    store = snapshot_store or get_price_snapshot_store()
    existing_history = store.load_history_points(product, limit=5)

    if extracted.amount is not None:
        current_price = extracted.amount
        price_source = "live"
        store.record_snapshot(product, url, current_price, currency, observed_at=observed_at or datetime.now(UTC))
    elif existing_history:
        current_price = existing_history[-1].value
        price_source = "historical"
    else:
        current_price = _fallback_current_price(seed, product.category, product.marketplace)
        price_source = "estimated"

    history = store.load_history_points(product, limit=5)

    if len(history) >= 2:
        observed_prices = [point.value for point in history]
        average_price = round(sum(observed_prices) / len(observed_prices), 2)
        lowest_price = round(min(observed_prices), 2)
        target_price = round((average_price * 0.4) + (lowest_price * 0.6), 2)
    else:
        volatility = CATEGORY_VOLATILITY.get(product.category, CATEGORY_VOLATILITY["general"])
        drift = ((seed % 11) - 5) / 100
        average_price = round(current_price * (1.11 + volatility + max(drift, 0)), 2)
        lowest_price = round(max(current_price * (0.84 - (volatility / 3) + min(drift, 0)), current_price * 0.66), 2)
        target_price = round((average_price * 0.38) + (lowest_price * 0.62), 2)
        history = existing_history if existing_history else _history_points(current_price, seed, volatility)

    preference_multipliers = {
        "aggressive": 1.05,
        "balanced": 1.0,
        "conservative": 0.95,
    }
    target_price = round(target_price * preference_multipliers.get(deal_preference, 1.0), 2)
    is_good_deal = current_price <= round(target_price * 1.01, 2)

    return PricingInsight(
        currentPrice=round(current_price, 2),
        averagePrice=average_price,
        lowestPrice=lowest_price,
        recommendedTargetPrice=target_price,
        currency=currency,
        isGoodDeal=is_good_deal,
        priceSource=price_source,
        history=history,
        marketplacePrices=marketplace_prices or [],
    )
