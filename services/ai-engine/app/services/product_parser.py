from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs, quote_plus, unquote, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import settings
from app.models.schemas import ProductIdentity
from app.services.adapters.registry import MarketplaceAdapter, resolve_marketplace


FIRST_PARTY_BRANDS = {
    "hm": "H&M",
    "zara": "Zara",
}

BRAND_CASE_OVERRIDES = {
    "adidas": "Adidas",
    "ajio": "Ajio",
    "amul": "Amul",
    "apple": "Apple",
    "asus": "ASUS",
    "babyhug": "Babyhug",
    "bestbuy": "Best Buy",
    "boat": "boAt",
    "croma": "Croma",
    "dell": "Dell",
    "firstcry": "FirstCry",
    "flipkart": "Flipkart",
    "google": "Google",
    "hm": "H&M",
    "h&m": "H&M",
    "hp": "HP",
    "iphone": "iPhone",
    "ipad": "iPad",
    "jiomart": "JioMart",
    "lg": "LG",
    "loreal": "L'Oreal",
    "macbook": "MacBook",
    "maybelline": "Maybelline",
    "meesho": "Meesho",
    "myntra": "Myntra",
    "nike": "Nike",
    "nothing": "Nothing",
    "nykaa": "Nykaa",
    "oneplus": "OnePlus",
    "puma": "Puma",
    "realme": "realme",
    "redmi": "Redmi",
    "reliance": "Reliance",
    "samsung": "Samsung",
    "sony": "Sony",
    "tatacliq": "Tata CLiQ",
    "vijaysales": "Vijay Sales",
    "xiaomi": "Xiaomi",
    "zara": "Zara",
}

LOWERCASE_TOKENS = {"a", "an", "and", "by", "for", "in", "of", "on", "the", "to", "with"}
UPPERCASE_TOKENS = {
    "4k",
    "5g",
    "ai",
    "bt",
    "cpu",
    "dslr",
    "fhd",
    "fps",
    "gpu",
    "hd",
    "hdd",
    "led",
    "oled",
    "pc",
    "ps5",
    "ram",
    "rgb",
    "rom",
    "ssd",
    "tv",
    "uhd",
    "usb",
    "wifi",
}

STOPWORDS = {
    "buy",
    "detail",
    "details",
    "dp",
    "gp",
    "html",
    "item",
    "items",
    "p",
    "page",
    "pd",
    "prd",
    "product",
    "productpage",
    "products",
    "shop",
    "site",
    "sku",
    "store",
}

CATEGORY_KEYWORDS = {
    "airpods": "electronics",
    "baby": "kids",
    "beauty": "beauty",
    "blazer": "fashion",
    "cleanser": "beauty",
    "conditioner": "beauty",
    "diaper": "kids",
    "dress": "fashion",
    "earbuds": "electronics",
    "foundation": "beauty",
    "fridge": "electronics",
    "galaxy": "electronics",
    "grocery": "grocery",
    "headphone": "electronics",
    "hoodie": "fashion",
    "iphone": "electronics",
    "jeans": "fashion",
    "jogger": "fashion",
    "kurta": "fashion",
    "kurti": "fashion",
    "laptop": "electronics",
    "lipstick": "beauty",
    "mask": "beauty",
    "milk": "grocery",
    "monitor": "electronics",
    "neckband": "electronics",
    "phone": "electronics",
    "polo": "fashion",
    "rice": "grocery",
    "rockerz": "electronics",
    "saree": "fashion",
    "serum": "beauty",
    "shampoo": "beauty",
    "shirt": "fashion",
    "shoe": "fashion",
    "shorts": "fashion",
    "skincare": "beauty",
    "smartphone": "electronics",
    "speaker": "electronics",
    "stroller": "kids",
    "tablet": "electronics",
    "tee": "fashion",
    "top": "fashion",
    "toy": "kids",
    "trouser": "fashion",
    "tv": "electronics",
    "watch": "electronics",
}

PRODUCT_PAGE_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
}


@dataclass(frozen=True)
class PageMetadata:
    name: str | None = None
    brand: str | None = None
    image: str | None = None
    category: str | None = None


@dataclass(frozen=True)
class ExtractionHints:
    name: str | None = None
    brand: str | None = None
    category: str | None = None
    product_id: str | None = None


@dataclass(frozen=True)
class ExtractionContext:
    url: str
    marketplace: MarketplaceAdapter
    path: str
    path_segments: tuple[str, ...]
    query_params: dict[str, list[str]]
    metadata: PageMetadata

    def first_query_value(self, *keys: str) -> str | None:
        for key in keys:
            values = self.query_params.get(key)
            if values and values[0].strip():
                return values[0].strip()
        return None


def _normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _strip_site_suffix(value: str, marketplace: str) -> str:
    cleaned = _normalize_space(unquote(value))
    cleaned = re.sub(r"\s*[|:-]\s*(?:buy|shop).*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(rf"\s*[|:-]\s*{re.escape(marketplace)}(?:\.[a-z]{{2,3}})?\s*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*[|:-]\s*(?:online shopping|official store).*$", "", cleaned, flags=re.IGNORECASE)
    return _normalize_space(cleaned)


def _format_token(token: str, position: int, total: int) -> str:
    lowered = token.lower()

    if lowered in BRAND_CASE_OVERRIDES:
        return BRAND_CASE_OVERRIDES[lowered]

    if lowered in UPPERCASE_TOKENS:
        return lowered.upper()

    if re.fullmatch(r"\d+(gb|tb|hz|mah|mp|w|ml|cm|mm|kg|g|l)", lowered):
        numeric_prefix = re.match(r"(\d+)", lowered)
        number = numeric_prefix.group(1)
        return f"{number}{lowered[len(number):].upper()}"

    if lowered in LOWERCASE_TOKENS and 0 < position < total - 1:
        return lowered

    if re.fullmatch(r"[a-z]{1,3}\d+[a-z0-9]*", lowered):
        return token.upper()

    if re.fullmatch(r"\d+[a-z]{1,3}", lowered):
        number = re.match(r"(\d+)", lowered).group(1)
        suffix = lowered[len(number):].upper()
        return f"{number}{suffix}"

    return lowered.capitalize()


def _polish_name(raw_name: str | None) -> str | None:
    if not raw_name:
        return None

    cleaned = unquote(raw_name)
    cleaned = re.sub(r"[+_/]+", " ", cleaned)
    cleaned = re.sub(r"(?i)\bproductpage\b", " ", cleaned)
    cleaned = re.sub(r"(?i)-p[0-9a-z]+(?:\.html)?$", " ", cleaned)
    cleaned = re.sub(r"(?i)\.p$", " ", cleaned)
    cleaned = re.sub(r"(?i)\.html?$", " ", cleaned)
    cleaned = re.sub(r"[-]+", " ", cleaned)
    cleaned = re.sub(r"[^\w&.\s]", " ", cleaned)
    cleaned = _normalize_space(cleaned)

    tokens = []
    for token in cleaned.split(" "):
        lowered = token.lower()
        if lowered in STOPWORDS:
            continue
        if re.fullmatch(r"(?:itm[a-z0-9-]*|sku[a-z0-9-]*|pid[a-z0-9-]*|ref[a-z0-9-]*|mp[a-z0-9-]*)", lowered):
            continue
        if re.fullmatch(r"[a-z0-9]{10,}", lowered) and any(char.isdigit() for char in lowered):
            continue
        if re.fullmatch(r"\d{6,}", lowered):
            continue
        tokens.append(token)

    if not tokens:
        return None

    formatted = " ".join(_format_token(token, index, len(tokens)) for index, token in enumerate(tokens))
    formatted = re.sub(r"\bTv\b", "TV", formatted)
    formatted = re.sub(r"\bHd\b", "HD", formatted)
    formatted = re.sub(r"\bUhd\b", "UHD", formatted)
    formatted = re.sub(r"\b(\d+)\s+(Gb|Tb|Hz|Mah|Mp|W|Ml|Cm|Mm|Kg|G|L)\b", lambda match: f"{match.group(1)}{match.group(2).upper()}", formatted)
    formatted = re.sub(r"\b(\d+)\s+K\b", lambda match: f"{match.group(1)}K", formatted)
    return _normalize_space(formatted)


def _sanitize_brand(value: str | None) -> str | None:
    if not value:
        return None

    cleaned = _polish_name(value)
    if not cleaned:
        return None

    token_count = len(cleaned.split(" "))
    return cleaned if token_count <= 3 else " ".join(cleaned.split(" ")[:3])


def _infer_brand(product_name: str | None) -> str | None:
    if not product_name:
        return None

    words = product_name.split(" ")
    if not words:
        return None

    brand = BRAND_CASE_OVERRIDES.get(words[0].lower())
    if brand:
        return brand

    if len(words) >= 2 and words[0].lower() == "best" and words[1].lower() == "buy":
        return "Best Buy"

    return words[0]


def _infer_category(text: str, fallback: str) -> str:
    lowered = text.lower()

    for keyword, category in CATEGORY_KEYWORDS.items():
        if keyword in lowered:
            return category

    return fallback


def _placeholder_image(marketplace: MarketplaceAdapter) -> str:
    return f"https://placehold.co/512x512/png?text={quote_plus(marketplace.label)}"


def _normalize_image(url: str, image: str | None) -> str | None:
    if not image:
        return None

    cleaned = image.strip()
    if not cleaned or cleaned.startswith("data:"):
        return None

    if cleaned.startswith("//"):
        return f"https:{cleaned}"

    return urljoin(url, cleaned)


def _extract_brand_from_json_ld(value: Any) -> str | None:
    if isinstance(value, str):
        return value

    if isinstance(value, dict):
        for key in ("name", "brand"):
            nested = value.get(key)
            if isinstance(nested, str) and nested.strip():
                return nested

    if isinstance(value, list):
        for item in value:
            extracted = _extract_brand_from_json_ld(item)
            if extracted:
                return extracted

    return None


def _extract_image_from_json_ld(value: Any) -> str | None:
    if isinstance(value, str):
        return value

    if isinstance(value, list):
        for item in value:
            if isinstance(item, str) and item.strip():
                return item

    return None


def _iter_product_objects(value: Any) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []

    if isinstance(value, list):
        for item in value:
            products.extend(_iter_product_objects(item))
        return products

    if not isinstance(value, dict):
        return products

    object_type = value.get("@type")
    if isinstance(object_type, str) and object_type.lower() == "product":
        products.append(value)
    elif isinstance(object_type, list) and any(str(item).lower() == "product" for item in object_type):
        products.append(value)

    for key in ("@graph", "mainEntity", "mainEntityOfPage", "itemListElement"):
        nested = value.get(key)
        if nested is not None:
            products.extend(_iter_product_objects(nested))

    return products


def _parse_html_metadata(url: str, marketplace: MarketplaceAdapter, html: str | None) -> PageMetadata:
    if not html:
        return PageMetadata()

    soup = BeautifulSoup(html, "html.parser")

    json_ld_name: str | None = None
    json_ld_brand: str | None = None
    json_ld_image: str | None = None
    json_ld_category: str | None = None

    for script in soup.find_all("script", attrs={"type": re.compile(r"application/ld\+json", re.IGNORECASE)}):
        payload = script.string or script.get_text(strip=True)
        if not payload:
            continue

        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError:
            continue

        for product in _iter_product_objects(parsed):
            json_ld_name = json_ld_name or product.get("name")
            json_ld_brand = json_ld_brand or _extract_brand_from_json_ld(product.get("brand"))
            json_ld_image = json_ld_image or _extract_image_from_json_ld(product.get("image"))
            json_ld_category = json_ld_category or product.get("category")
            if json_ld_name and json_ld_brand and json_ld_image:
                break

    def meta_content(*pairs: tuple[str, str]) -> str | None:
        for attribute, value in pairs:
            tag = soup.find("meta", attrs={attribute: value})
            if tag and tag.get("content"):
                return tag["content"].strip()
        return None

    title_tag = soup.find("title")
    title_value = title_tag.get_text(strip=True) if title_tag else None

    return PageMetadata(
        name=_strip_site_suffix(
            json_ld_name
            or meta_content(("property", "og:title"), ("name", "twitter:title"), ("name", "title"))
            or title_value
            or "",
            marketplace.label,
        )
        or None,
        brand=_sanitize_brand(
            json_ld_brand
            or meta_content(("property", "product:brand"), ("name", "brand"), ("itemprop", "brand"))
        ),
        image=_normalize_image(
            url,
            json_ld_image
            or meta_content(("property", "og:image"), ("name", "twitter:image"), ("itemprop", "image")),
        ),
        category=_polish_name(
            json_ld_category
            or meta_content(("property", "product:category"), ("name", "category"), ("itemprop", "category"))
        ),
    )


def _segment_before(path_segments: tuple[str, ...], markers: set[str]) -> str | None:
    lowered = [segment.lower() for segment in path_segments]
    for index, segment in enumerate(lowered):
        if segment in markers and index > 0:
            return path_segments[index - 1]
        if any(segment.startswith(marker) for marker in markers if marker.endswith("-")) and index > 0:
            return path_segments[index - 1]
    return None


def _last_descriptive_segment(path_segments: tuple[str, ...], excluded: set[str] | None = None) -> str | None:
    excluded = excluded or set()
    for segment in reversed(path_segments):
        lowered = segment.lower()
        if lowered in excluded or lowered in STOPWORDS:
            continue
        if re.fullmatch(r"\d{6,}(?:\.p)?", lowered):
            continue
        if re.fullmatch(r"p-[a-z0-9-]+", lowered):
            continue
        return segment
    return None


def _extract_amazon(ctx: ExtractionContext) -> ExtractionHints:
    product_id = None
    match = re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})", ctx.path, re.IGNORECASE)
    if match:
        product_id = match.group(1).upper()

    slug = _segment_before(ctx.path_segments, {"dp", "product"})
    query_name = ctx.first_query_value("keywords", "k")

    return ExtractionHints(name=_polish_name(query_name or slug), product_id=product_id)


def _extract_flipkart(ctx: ExtractionContext) -> ExtractionHints:
    slug = _segment_before(ctx.path_segments, {"p"})
    product_id = ctx.first_query_value("pid")
    return ExtractionHints(name=_polish_name(slug), product_id=product_id)


def _extract_ajio(ctx: ExtractionContext) -> ExtractionHints:
    slug = _segment_before(ctx.path_segments, {"p"})
    return ExtractionHints(name=_polish_name(slug))


def _extract_myntra(ctx: ExtractionContext) -> ExtractionHints:
    category = ctx.path_segments[0] if ctx.path_segments else None
    brand = ctx.path_segments[1] if len(ctx.path_segments) > 1 else None
    slug = ctx.path_segments[2] if len(ctx.path_segments) > 2 else _segment_before(ctx.path_segments, {"buy"})
    product_id = ctx.path_segments[3] if len(ctx.path_segments) > 3 and re.fullmatch(r"\d{6,}", ctx.path_segments[3]) else None

    return ExtractionHints(
        name=_polish_name(slug),
        brand=_sanitize_brand(brand),
        category=_polish_name(category),
        product_id=product_id,
    )


def _extract_nykaa(ctx: ExtractionContext) -> ExtractionHints:
    slug = _segment_before(ctx.path_segments, {"p"})
    product_id = ctx.first_query_value("skuId") or ctx.path_segments[-1] if ctx.path_segments else None
    return ExtractionHints(name=_polish_name(slug), product_id=product_id)


def _extract_tatacliq(ctx: ExtractionContext) -> ExtractionHints:
    slug = _last_descriptive_segment(ctx.path_segments[:-1], {"luxury"}) if len(ctx.path_segments) > 1 else None
    product_id = ctx.path_segments[-1] if ctx.path_segments and ctx.path_segments[-1].lower().startswith("p-") else None
    return ExtractionHints(name=_polish_name(slug), product_id=product_id)


def _extract_meesho(ctx: ExtractionContext) -> ExtractionHints:
    slug = _segment_before(ctx.path_segments, {"p"})
    return ExtractionHints(name=_polish_name(slug))


def _extract_croma(ctx: ExtractionContext) -> ExtractionHints:
    slug = _segment_before(ctx.path_segments, {"p"})
    return ExtractionHints(name=_polish_name(slug))


def _extract_reliance_digital(ctx: ExtractionContext) -> ExtractionHints:
    slug = _segment_before(ctx.path_segments, {"p"})
    if not slug and len(ctx.path_segments) >= 2:
        slug = ctx.path_segments[-2]
    return ExtractionHints(name=_polish_name(slug))


def _extract_vijay_sales(ctx: ExtractionContext) -> ExtractionHints:
    slug = _last_descriptive_segment(ctx.path_segments[:-1]) if len(ctx.path_segments) > 1 else _last_descriptive_segment(ctx.path_segments)
    return ExtractionHints(name=_polish_name(slug))


def _extract_snapdeal(ctx: ExtractionContext) -> ExtractionHints:
    slug = _last_descriptive_segment(ctx.path_segments[:-1], {"product"}) if len(ctx.path_segments) > 1 else None
    return ExtractionHints(name=_polish_name(slug))


def _extract_jiomart(ctx: ExtractionContext) -> ExtractionHints:
    category = ctx.path_segments[1] if len(ctx.path_segments) > 1 and ctx.path_segments[0].lower() == "p" else None
    slug = _last_descriptive_segment(ctx.path_segments[:-1], {"p", "groceries", "electronics", "fashion"})
    return ExtractionHints(name=_polish_name(slug), category=_polish_name(category))


def _extract_firstcry(ctx: ExtractionContext) -> ExtractionHints:
    slug = _last_descriptive_segment(ctx.path_segments[:-2], {"product-detail"}) if len(ctx.path_segments) > 2 else None
    if not slug and len(ctx.path_segments) >= 2:
        slug = ctx.path_segments[-2]
    return ExtractionHints(name=_polish_name(slug))


def _extract_hm(ctx: ExtractionContext) -> ExtractionHints:
    product_id_match = re.search(r"productpage\.(\d+)", ctx.path, re.IGNORECASE)
    fallback_name = None
    if product_id_match:
        fallback_name = f"H&M Product {product_id_match.group(1)}"

    return ExtractionHints(
        name=fallback_name,
        brand=FIRST_PARTY_BRANDS["hm"],
        category="fashion",
        product_id=product_id_match.group(1) if product_id_match else None,
    )


def _extract_zara(ctx: ExtractionContext) -> ExtractionHints:
    slug = _last_descriptive_segment(ctx.path_segments)
    cleaned = None
    if slug:
        cleaned = re.sub(r"(?i)-p[0-9a-z]+(?:\.html)?$", "", slug)
    return ExtractionHints(
        name=_polish_name(cleaned),
        brand=FIRST_PARTY_BRANDS["zara"],
        category="fashion",
    )


def _extract_best_buy(ctx: ExtractionContext) -> ExtractionHints:
    slug = _last_descriptive_segment(ctx.path_segments[:-1], {"site"}) if len(ctx.path_segments) > 1 else None
    product_id = ctx.first_query_value("skuId")
    if not product_id and ctx.path_segments:
        id_match = re.search(r"(\d{6,})", ctx.path_segments[-1])
        product_id = id_match.group(1) if id_match else None
    return ExtractionHints(name=_polish_name(slug), product_id=product_id)


def _extract_generic(ctx: ExtractionContext) -> ExtractionHints:
    slug = _last_descriptive_segment(ctx.path_segments, {"p", "product", "products", "site"})
    return ExtractionHints(name=_polish_name(slug))


EXTRACTORS = {
    "amazon": _extract_amazon,
    "flipkart": _extract_flipkart,
    "ajio": _extract_ajio,
    "myntra": _extract_myntra,
    "nykaa": _extract_nykaa,
    "tatacliq": _extract_tatacliq,
    "meesho": _extract_meesho,
    "croma": _extract_croma,
    "reliance-digital": _extract_reliance_digital,
    "vijay-sales": _extract_vijay_sales,
    "snapdeal": _extract_snapdeal,
    "jiomart": _extract_jiomart,
    "firstcry": _extract_firstcry,
    "hm": _extract_hm,
    "zara": _extract_zara,
    "best-buy": _extract_best_buy,
}


async def fetch_product_page(url: str) -> str | None:
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            headers=PRODUCT_PAGE_HEADERS,
            timeout=settings.request_timeout_seconds,
        ) as client:
            response = await client.get(url)
    except httpx.HTTPError:
        return None

    if not response.is_success:
        return None

    content_type = response.headers.get("content-type", "")
    if "html" not in content_type.lower():
        return None

    return response.text


def parse_product_identity(url: str, html: str | None = None) -> ProductIdentity:
    parsed_url = urlparse(url)
    marketplace = resolve_marketplace(url)
    metadata = _parse_html_metadata(url, marketplace, html)
    context = ExtractionContext(
        url=url,
        marketplace=marketplace,
        path=parsed_url.path,
        path_segments=tuple(segment for segment in parsed_url.path.split("/") if segment),
        query_params=parse_qs(parsed_url.query),
        metadata=metadata,
    )

    extractor = EXTRACTORS.get(marketplace.slug, _extract_generic)
    hints = extractor(context)
    fallback_name = _extract_generic(context).name or (
        f"{marketplace.label} Product {hints.product_id}" if hints.product_id else "Product Research"
    )

    product_name = metadata.name or hints.name or fallback_name
    product_name = _polish_name(product_name) or fallback_name

    brand = (
        metadata.brand
        or hints.brand
        or _infer_brand(product_name)
        or FIRST_PARTY_BRANDS.get(marketplace.slug)
        or "Unknown"
    )

    category_source = " ".join(
        value
        for value in [
            metadata.category,
            hints.category,
            marketplace.category_hint,
            parsed_url.path,
            product_name,
        ]
        if value
    )

    image = metadata.image or _placeholder_image(marketplace)

    return ProductIdentity(
        marketplace=marketplace.label,
        name=product_name,
        brand=brand,
        category=_infer_category(category_source, marketplace.category_hint),
        image=image,
    )
