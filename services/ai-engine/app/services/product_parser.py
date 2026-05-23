import re
from urllib.parse import urlparse

from app.models.schemas import ProductIdentity
from app.services.adapters.registry import resolve_marketplace


PLACEHOLDER_IMAGE = "https://placehold.co/512x512/png"


def _title_from_slug(path: str) -> str:
    slug = path.rstrip("/").split("/")[-1]
    slug = re.sub(r"[_-]+", " ", slug)
    slug = re.sub(r"\b(?:dp|p|product|item|shop|buy)\b", " ", slug, flags=re.IGNORECASE)
    slug = re.sub(r"\b[a-z0-9]{8,}\b", " ", slug, flags=re.IGNORECASE)
    slug = re.sub(r"\s+", " ", slug).strip()
    return slug.title() if slug else "Product Research"


def _infer_brand(product_name: str) -> str:
    return product_name.split(" ")[0] if product_name else "Unknown"


def _infer_category(path: str, fallback: str) -> str:
    lowered = path.lower()
    keywords = {
        "dress": "fashion",
        "shirt": "fashion",
        "shoe": "fashion",
        "lipstick": "beauty",
        "serum": "beauty",
        "laptop": "electronics",
        "phone": "electronics",
        "headphone": "electronics",
        "grocery": "grocery",
        "baby": "kids",
    }

    for keyword, category in keywords.items():
        if keyword in lowered:
            return category

    return fallback


def parse_product_identity(url: str) -> ProductIdentity:
    parsed_url = urlparse(url)
    marketplace = resolve_marketplace(url)
    product_name = _title_from_slug(parsed_url.path)
    brand = _infer_brand(product_name)
    category = _infer_category(parsed_url.path, marketplace.category_hint)

    return ProductIdentity(
        marketplace=marketplace.label,
        name=product_name,
        brand=brand,
        category=category,
        image=PLACEHOLDER_IMAGE,
    )
