from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
import re
from urllib.parse import parse_qs, quote_plus, unquote, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import settings
from app.models.schemas import MarketplacePrice, PricePoint, PricingInsight, ProductIdentity, ResearchPreferences
from app.services.adapters.registry import MarketplaceAdapter, resolve_marketplace, resolve_marketplace_slug
from app.services.price_intelligence import _parse_price_text, build_pricing_insight
from app.services.product_parser import (
    PRODUCT_PAGE_HEADERS,
    _infer_brand,
    _infer_category,
    _sanitize_brand,
    parse_product_identity,
)


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
GENERIC_CANDIDATE_NAMES = {
    "online store",
    "product research",
}
NATIVE_SEARCH_MARKETPLACES = {"amazon", "nykaa", "myntra", "ajio"}
ACCESSORY_TOKENS = {
    "adapter",
    "band",
    "bumper",
    "cable",
    "camera",
    "case",
    "charger",
    "cover",
    "dock",
    "earbuds",
    "film",
    "flash",
    "glass",
    "holder",
    "keyboard",
    "laptop",
    "lens",
    "mouse",
    "powerbank",
    "protector",
    "screen",
    "skin",
    "speaker",
    "stand",
    "strap",
    "stylus",
    "tempered",
    "tripod",
    "usb",
    "wallet",
    "watch",
}
MODEL_FAMILY_TOKENS = {
    "airpods",
    "galaxy",
    "iphone",
    "ipad",
    "macbook",
    "pixel",
    "redmi",
    "rog",
}
NATIVE_MATCH_THRESHOLDS = {
    "amazon": 0.5,
    "ajio": 0.42,
    "myntra": 0.42,
    "nykaa": 0.42,
}


@dataclass(frozen=True)
class ComparisonCandidate:
    adapter: MarketplaceAdapter
    product: ProductIdentity
    pricing: PricingInsight
    url: str
    match_score: float


@dataclass(frozen=True)
class CandidateLookupResult:
    candidate: ComparisonCandidate | None
    note: str | None = None


@dataclass(frozen=True)
class NativeSearchResult:
    name: str
    url: str
    price: float
    currency: str
    brand: str | None = None
    category: str | None = None


def _search_phrase(product: ProductIdentity) -> str:
    phrase = product.name.strip()
    if not phrase.lower().startswith(product.brand.lower()):
        phrase = f"{product.brand} {phrase}"
    return " ".join(token for token in phrase.split() if token)


def _search_queries(adapter: MarketplaceAdapter, product: ProductIdentity) -> list[str]:
    primary_domain = adapter.domains[0]
    phrase = _search_phrase(product)
    queries = [
        f'site:{primary_domain} "{phrase}"',
        f'site:{primary_domain} "{product.brand}" "{product.name}"',
        f"site:{primary_domain} {phrase}",
    ]

    if product.category != "general":
        queries.append(f'site:{primary_domain} "{phrase}" {product.category}')

    seen: set[str] = set()
    ordered: list[str] = []
    for query in queries:
        normalized = " ".join(query.split())
        if normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered


def _native_search_url(adapter: MarketplaceAdapter, product: ProductIdentity) -> str | None:
    phrase = _search_phrase(product)
    if adapter.slug == "amazon":
        return f"https://www.amazon.in/s?k={quote_plus(phrase)}"
    if adapter.slug == "nykaa":
        return f"https://www.nykaa.com/search/result/?q={quote_plus(phrase)}"
    if adapter.slug == "myntra":
        slug = re.sub(r"[^a-z0-9]+", "-", phrase.lower()).strip("-")
        return f"https://www.myntra.com/{slug}"
    if adapter.slug == "ajio":
        return f"https://www.ajio.com/search/?text={quote_plus(phrase)}"
    return None


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


def _extract_balanced_fragment(text: str, start_idx: int, open_char: str, close_char: str) -> str | None:
    depth = 0
    in_string = False
    escape = False

    for position, char in enumerate(text[start_idx:], start=start_idx):
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
            continue

        if char == open_char:
            depth += 1
        elif char == close_char:
            depth -= 1
            if depth == 0:
                return text[start_idx : position + 1]

    return None


def _find_json_payload_start(html: str, key: str, opening_char: str) -> int:
    pattern = re.compile(rf'"{re.escape(key)}"\s*:\s*{re.escape(opening_char)}')
    match = pattern.search(html)
    if not match:
        return -1
    return html.find(opening_char, match.start())


def _extract_amazon_card_title(card: BeautifulSoup) -> str:
    title_node = card.select_one("h2")
    explicit_title = title_node.get_text(" ", strip=True) if title_node else ""
    if explicit_title and len(explicit_title.split()) > 2:
        return explicit_title

    parts = [part.strip() for part in card.get_text(" | ", strip=True).split(" | ") if part.strip()]
    if not parts:
        return explicit_title

    stop_patterns = (
        re.compile(r"^\d(?:\.\d)?$"),
        re.compile(r"^\(?\d[\d.,Kk+]*\)?$"),
    )
    stop_phrases = (
        "out of 5 stars",
        "bought in past month",
        "delivery",
        "m.r.p",
        "add to cart",
        "price, product page",
        "save extra",
        "limited time deal",
    )
    title_parts: list[str] = []
    for part in parts:
        lowered = part.lower()
        if any(phrase in lowered for phrase in stop_phrases):
            break
        if any(pattern.match(part) for pattern in stop_patterns):
            break
        title_parts.append(part)
        if len(title_parts) >= 8:
            break

    if title_parts:
        return " ".join(title_parts)
    return explicit_title


def _parse_amazon_search_results(html: str) -> list[NativeSearchResult]:
    soup = BeautifulSoup(html, "html.parser")
    results: list[NativeSearchResult] = []

    for card in soup.select('[data-component-type="s-search-result"]'):
        link = card.select_one('a.a-link-normal[href*="/dp/"]')
        price_node = card.select_one(".a-price .a-offscreen")
        if not link or not price_node:
            continue

        title = _extract_amazon_card_title(card)
        if not title:
            continue

        parsed_price = _parse_price_text(price_node.get_text(" ", strip=True), "INR")
        if parsed_price.amount is None:
            continue

        results.append(
            NativeSearchResult(
                name=title,
                url=urljoin("https://www.amazon.in", link.get("href", "")),
                price=parsed_price.amount,
                currency=parsed_price.currency or "INR",
            )
        )
        if len(results) >= 10:
            break

    return results


def _parse_nykaa_search_results(html: str) -> list[NativeSearchResult]:
    soup = BeautifulSoup(html, "html.parser")
    results: list[NativeSearchResult] = []
    seen: set[str] = set()

    for link in soup.select('a[href*="/p/"]'):
        href = link.get("href")
        image_node = link.find("img", alt=True)
        card = link.find_parent(
            "div",
            class_=lambda value: isinstance(value, str) and (
                "productWrapper" in value or "css-ifdzs8" in value or "css-d5z3ro" in value
            ),
        ) or link.parent
        title_node = card.select_one("h2") if card else link.find("h2")
        title = ""
        if image_node and image_node.get("alt"):
            title = image_node.get("alt", "").strip()
        elif title_node:
            title = title_node.get_text(" ", strip=True)

        if not href or not title:
            continue
        absolute_url = urljoin("https://www.nykaa.com", href)
        if absolute_url in seen:
            continue

        current_price = None
        search_root = card if card else link
        for selector in ("span.css-111z9ua", "span[data-testid='price-final']", "div[class*='price'] span"):
            node = search_root.select_one(selector)
            if not node:
                continue
            parsed = _parse_price_text(node.get_text(" ", strip=True), "INR")
            if parsed.amount is not None:
                current_price = parsed
                break
        if current_price is None:
            for span in search_root.find_all("span"):
                parsed = _parse_price_text(span.get_text(" ", strip=True), "INR")
                if parsed.amount is not None:
                    current_price = parsed
                    break
        if current_price is None or current_price.amount is None:
            continue

        results.append(
            NativeSearchResult(
                name=title,
                url=absolute_url,
                price=current_price.amount,
                currency=current_price.currency or "INR",
            )
        )
        seen.add(absolute_url)
        if len(results) >= 10:
            break

    return results


def _parse_myntra_search_results(html: str) -> list[NativeSearchResult]:
    payload_start = _find_json_payload_start(html, "products", "[")
    if payload_start == -1:
        return []
    payload = _extract_balanced_fragment(html, payload_start, "[", "]")
    if not payload:
        return []

    try:
        products = json.loads(payload)
    except json.JSONDecodeError:
        return []

    results: list[NativeSearchResult] = []
    for product in products:
        price = product.get("price")
        name = product.get("productName") or product.get("product")
        landing_page_url = product.get("landingPageUrl")
        if not name or not landing_page_url or not isinstance(price, (int, float)):
            continue

        results.append(
            NativeSearchResult(
                name=str(name),
                url=urljoin("https://www.myntra.com/", str(landing_page_url)),
                price=float(price),
                currency="INR",
                brand=_sanitize_brand(str(product.get("brand") or "")) or None,
                category="fashion",
            )
        )
        if len(results) >= 12:
            break

    return results


def _parse_ajio_search_results(html: str) -> list[NativeSearchResult]:
    payload_start = _find_json_payload_start(html, "grid", "{")
    if payload_start == -1:
        return []
    payload = _extract_balanced_fragment(html, payload_start, "{", "}")
    if not payload:
        return []

    try:
        grid = json.loads(payload)
    except json.JSONDecodeError:
        return []

    results: list[NativeSearchResult] = []
    entities = grid.get("entities", {})
    for entry in grid.get("results", []):
        code = entry
        product = {}
        if isinstance(entry, dict):
            code = entry.get("code") or entry.get("entityId") or entry.get("id")
            product = entry
        if code is not None and not product:
            product = entities.get(str(code)) or entities.get(code) or {}
        name = product.get("name")
        relative_url = product.get("url")
        offer_price = (product.get("offerPrice") or {}).get("value")
        base_price = (product.get("price") or {}).get("value")
        price = offer_price or base_price
        if not name or not relative_url or not isinstance(price, (int, float)):
            continue

        results.append(
            NativeSearchResult(
                name=str(name),
                url=urljoin("https://www.ajio.com", str(relative_url)),
                price=float(price),
                currency="INR",
                brand=_sanitize_brand(str(((product.get("fnlColorVariantData") or {}).get("brandName")) or "")) or None,
                category="fashion",
            )
        )
        if len(results) >= 12:
            break

    return results


def _native_search_results(adapter: MarketplaceAdapter, html: str) -> list[NativeSearchResult]:
    if adapter.slug == "amazon":
        return _parse_amazon_search_results(html)
    if adapter.slug == "nykaa":
        return _parse_nykaa_search_results(html)
    if adapter.slug == "myntra":
        return _parse_myntra_search_results(html)
    if adapter.slug == "ajio":
        return _parse_ajio_search_results(html)
    return []


def _native_result_product(adapter: MarketplaceAdapter, result: NativeSearchResult) -> ProductIdentity:
    parsed = parse_product_identity(result.url)
    derived_brand = _sanitize_brand(result.brand or _infer_brand(result.name)) or parsed.brand
    category_source = " ".join(
        value for value in [result.category, parsed.category, adapter.category_hint, result.name] if value
    )
    return ProductIdentity(
        marketplace=parsed.marketplace,
        name=result.name,
        brand=derived_brand,
        category=_infer_category(category_source, parsed.category or adapter.category_hint),
        image=parsed.image,
    )


def _native_result_pricing(result: NativeSearchResult, original_price: float) -> PricingInsight:
    price = round(result.price, 2)
    return PricingInsight(
        currentPrice=price,
        averagePrice=price,
        lowestPrice=price,
        recommendedTargetPrice=price,
        currency=result.currency,
        isGoodDeal=price <= original_price,
        priceSource="live",
        history=[PricePoint(label="Now", value=price)],
        marketplacePrices=[],
    )


def _normalize_marketplace_url(adapter: MarketplaceAdapter, url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path

    if adapter.slug == "amazon":
        match = re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})", path, re.IGNORECASE)
        if match:
            path = f"/dp/{match.group(1).upper()}"
            return f"{parsed.scheme}://{parsed.netloc}{path}"

    normalized = parsed._replace(fragment="", query="")
    return normalized.geturl()


def _is_probable_product_url(adapter: MarketplaceAdapter, url: str) -> bool:
    path = (urlparse(url).path or "").lower()

    if adapter.slug == "amazon":
        return "/dp/" in path or "/gp/product/" in path
    if adapter.slug in {"flipkart", "ajio", "nykaa", "croma", "jiomart"}:
        return "/p/" in path
    if adapter.slug == "reliance-digital":
        return "/p/" in path or "/product/" in path
    if adapter.slug == "myntra":
        return path.endswith("/buy") or bool(re.search(r"/\d{6,}/buy$", path))
    if adapter.slug == "tatacliq":
        return "/p-" in path or path.endswith(".html")
    if adapter.slug == "meesho":
        return "/p/" in path
    if adapter.slug == "vijay-sales":
        return bool(re.search(r"/\d{5,}$", path))
    if adapter.slug == "snapdeal":
        return "/product/" in path
    if adapter.slug == "firstcry":
        return path.endswith("/product-detail")
    if adapter.slug == "hm":
        return "productpage." in path
    if adapter.slug == "zara":
        return bool(re.search(r"-p[0-9a-z]+(?:\.html)?$", path))
    if adapter.slug == "best-buy":
        return "/site/" in path and ".p" in path
    return True


def _extract_marketplace_urls(html: str, adapter: MarketplaceAdapter) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    probable_urls: list[str] = []
    fallback_urls: list[str] = []
    seen: set[str] = set()

    for link in soup.find_all("a", href=True):
        resolved = _unwrap_duckduckgo_href(link["href"])
        if not resolved:
            continue

        hostname = (urlparse(resolved).hostname or "").lower()
        if not any(hostname.endswith(domain) for domain in adapter.domains):
            continue

        normalized = _normalize_marketplace_url(adapter, resolved)
        if normalized in seen:
            continue

        seen.add(normalized)
        if _is_probable_product_url(adapter, normalized):
            probable_urls.append(normalized)
        else:
            fallback_urls.append(normalized)

        if len(probable_urls) >= 4:
            break

    return probable_urls + fallback_urls[: max(0, 4 - len(probable_urls))]


async def _search_marketplace_urls(
    client: httpx.AsyncClient,
    adapter: MarketplaceAdapter,
    product: ProductIdentity,
) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()

    for query in _search_queries(adapter, product):
        response = await client.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query, "kl": "in-en"},
            headers=SEARCH_HEADERS,
        )

        if not response.is_success:
            continue

        for url in _extract_marketplace_urls(response.text, adapter):
            if url in seen:
                continue
            seen.add(url)
            urls.append(url)
            if len(urls) >= 6:
                return urls

    return urls


async def _fetch_marketplace_html(client: httpx.AsyncClient, url: str) -> str | None:
    _, html = await _fetch_marketplace_page(client, url)
    return html


async def _fetch_marketplace_page(client: httpx.AsyncClient, url: str) -> tuple[int | None, str | None]:
    try:
        response = await client.get(url, headers=PRODUCT_PAGE_HEADERS)
    except httpx.HTTPError:
        return None, None

    if not response.is_success:
        return response.status_code, None

    content_type = response.headers.get("content-type", "")
    if "html" not in content_type.lower():
        return response.status_code, None

    return response.status_code, response.text


def _price_status(current_price: float | None, original_price: float, is_original_listing: bool) -> str:
    if is_original_listing:
        return "current"
    if current_price is None:
        return "unavailable"

    delta = round(current_price - original_price, 2)
    if abs(delta) <= max(original_price * 0.005, 1):
        return "same"
    return "cheaper" if delta < 0 else "higher"


def _looks_generic_candidate(adapter: MarketplaceAdapter, product: ProductIdentity) -> bool:
    normalized_name = product.name.strip().lower()
    normalized_brand = product.brand.strip().lower()
    adapter_name = adapter.label.strip().lower()

    if not normalized_name or normalized_name in GENERIC_CANDIDATE_NAMES:
        return True
    if normalized_name == adapter_name:
        return True
    if normalized_brand in {"unknown", adapter_name} and normalized_name.startswith(adapter_name):
        return True
    return False


def _important_tokens(product: ProductIdentity) -> set[str]:
    tokens = _tokenize_name(f"{product.brand} {product.name}")
    important = {token for token in tokens if any(char.isdigit() for char in token)}
    important.update(token for token in tokens if token in MODEL_FAMILY_TOKENS)
    return important


def _looks_accessory_match(target: ProductIdentity, candidate: ProductIdentity) -> bool:
    if target.category != "electronics":
        return False

    target_tokens = _tokenize_name(f"{target.brand} {target.name}")
    candidate_tokens = _tokenize_name(f"{candidate.brand} {candidate.name}")
    return bool(candidate_tokens & ACCESSORY_TOKENS) and not bool(target_tokens & ACCESSORY_TOKENS)


def _passes_match_guardrails(target: ProductIdentity, candidate: ProductIdentity) -> bool:
    target_brand = _sanitize_brand(target.brand) or target.brand
    candidate_brand = _sanitize_brand(candidate.brand) or candidate.brand
    if (
        target_brand
        and candidate_brand
        and target_brand.lower() != "unknown"
        and candidate_brand.lower() != "unknown"
        and target_brand.lower() != candidate_brand.lower()
    ):
        return False

    if _looks_accessory_match(target, candidate):
        return False

    important_tokens = _important_tokens(target)
    if important_tokens:
        candidate_tokens = _tokenize_name(f"{candidate.brand} {candidate.name}")
        if not (important_tokens & candidate_tokens):
            return False

    if target.category != "general" and candidate.category != "general" and target.category != candidate.category:
        return False

    return True


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
) -> CandidateLookupResult:
    native_search_url = _native_search_url(adapter, target_product)
    if adapter.slug in NATIVE_SEARCH_MARKETPLACES and native_search_url:
        native_status, native_html = await _fetch_marketplace_page(client, native_search_url)
        if native_status == 403:
            return CandidateLookupResult(
                candidate=None,
                note=f"{adapter.label} blocked live search requests from the backend on this attempt.",
            )
        if native_html:
            native_candidates: list[ComparisonCandidate] = []
            native_results = _native_search_results(adapter, native_html)
            saw_native_results = bool(native_results)
            for result in native_results:
                candidate_product = _native_result_product(adapter, result)
                if _looks_generic_candidate(adapter, candidate_product):
                    continue
                if not _passes_match_guardrails(target_product, candidate_product):
                    continue

                match_score = _name_similarity(target_product, candidate_product)
                if match_score < NATIVE_MATCH_THRESHOLDS.get(adapter.slug, 0.4):
                    continue

                native_candidates.append(
                    ComparisonCandidate(
                        adapter=adapter,
                        product=candidate_product,
                        pricing=_native_result_pricing(result, original_price),
                        url=result.url,
                        match_score=match_score,
                    )
                )

            if native_candidates:
                native_candidates.sort(
                    key=lambda item: (
                        -item.match_score,
                        abs(item.pricing.current_price - original_price),
                    )
                )
                return CandidateLookupResult(candidate=native_candidates[0])
            if saw_native_results:
                return CandidateLookupResult(
                    candidate=None,
                    note=f"{adapter.label} search returned unrelated or accessory results for this product.",
                )

    urls = await _search_marketplace_urls(client, adapter, target_product)
    if not urls:
        return CandidateLookupResult(candidate=None, note=f"No live {adapter.label} product URLs were discovered.")

    best_candidate: ComparisonCandidate | None = None
    saw_blocked_product_page = False

    for url in urls:
        if not _is_probable_product_url(adapter, url):
            continue

        status_code, html = await _fetch_marketplace_page(client, url)
        if status_code == 403:
            saw_blocked_product_page = True
        if not html:
            continue

        candidate_product = parse_product_identity(url, html=html)
        if _looks_generic_candidate(adapter, candidate_product):
            continue
        if not _passes_match_guardrails(target_product, candidate_product):
            continue

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

    if best_candidate is not None:
        return CandidateLookupResult(candidate=best_candidate)
    if saw_blocked_product_page:
        return CandidateLookupResult(
            candidate=None,
            note=f"{adapter.label} blocked live product-page fetches from the backend on this attempt.",
        )
    return CandidateLookupResult(candidate=None, note=f"No close live {adapter.label} match was found.")


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
    should_recover_original = pricing.price_source != "live" and original_adapter.slug in NATIVE_SEARCH_MARKETPLACES
    if not remaining_adapters and not should_recover_original:
        return items

    timeout = httpx.Timeout(settings.request_timeout_seconds)
    semaphore = asyncio.Semaphore(4)

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=SEARCH_HEADERS) as client:
        if should_recover_original:
            recovered_original = await _best_marketplace_candidate(client, original_adapter, product, original_price)
            if recovered_original.candidate:
                original_price = recovered_original.candidate.pricing.current_price
                recovered_original_for_row = ComparisonCandidate(
                    adapter=recovered_original.candidate.adapter,
                    product=recovered_original.candidate.product,
                    pricing=recovered_original.candidate.pricing,
                    url=product_url,
                    match_score=recovered_original.candidate.match_score,
                )
                items[0] = _to_marketplace_price(
                    original_adapter,
                    recovered_original_for_row,
                    original_price,
                    is_original_listing=True,
                    note="Current listing price was recovered from live marketplace search results.",
                )

        async def compare(adapter: MarketplaceAdapter) -> MarketplacePrice:
            async with semaphore:
                try:
                    lookup = await _best_marketplace_candidate(client, adapter, product, original_price)
                except Exception:
                    lookup = CandidateLookupResult(candidate=None, note=f"{adapter.label} comparison failed unexpectedly.")

                if not lookup.candidate:
                    return _unavailable_marketplace_price(
                        adapter,
                        lookup.note or f"No close live {adapter.label} match was found.",
                    )

                return _to_marketplace_price(adapter, lookup.candidate, original_price)

        items.extend(await asyncio.gather(*(compare(adapter) for adapter in remaining_adapters)))

    return _sorted_marketplace_prices(items)
