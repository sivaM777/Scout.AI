from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class MarketplaceAdapter:
    slug: str
    label: str
    domains: tuple[str, ...]
    category_hint: str


SUPPORTED_MARKETPLACES: tuple[MarketplaceAdapter, ...] = (
    MarketplaceAdapter("amazon", "Amazon", ("amazon.in", "amazon.com", "amzn.in"), "general"),
    MarketplaceAdapter("flipkart", "Flipkart", ("flipkart.com", "dl.flipkart.com"), "general"),
    MarketplaceAdapter("ajio", "Ajio", ("ajio.com",), "fashion"),
    MarketplaceAdapter("myntra", "Myntra", ("myntra.com",), "fashion"),
    MarketplaceAdapter("nykaa", "Nykaa", ("nykaa.com",), "beauty"),
    MarketplaceAdapter("tatacliq", "Tata CLiQ", ("tatacliq.com",), "general"),
    MarketplaceAdapter("meesho", "Meesho", ("meesho.com",), "fashion"),
    MarketplaceAdapter("croma", "Croma", ("croma.com",), "electronics"),
    MarketplaceAdapter("reliance-digital", "Reliance Digital", ("reliancedigital.in",), "electronics"),
    MarketplaceAdapter("vijay-sales", "Vijay Sales", ("vijaysales.com",), "electronics"),
    MarketplaceAdapter("snapdeal", "Snapdeal", ("snapdeal.com",), "general"),
    MarketplaceAdapter("jiomart", "JioMart", ("jiomart.com",), "grocery"),
    MarketplaceAdapter("firstcry", "FirstCry", ("firstcry.com",), "kids"),
    MarketplaceAdapter("hm", "H&M", ("hm.com",), "fashion"),
    MarketplaceAdapter("zara", "Zara", ("zara.com",), "fashion"),
    MarketplaceAdapter("best-buy", "Best Buy", ("bestbuy.com",), "electronics"),
    MarketplaceAdapter("ebay", "eBay", ("ebay.com", "ebay.in"), "general"),
)

GENERIC_MARKETPLACE = MarketplaceAdapter("generic", "Online Store", tuple(), "general")


def resolve_marketplace(url: str) -> MarketplaceAdapter:
    hostname = urlparse(url).hostname or ""

    for adapter in SUPPORTED_MARKETPLACES:
        if any(hostname.endswith(domain) for domain in adapter.domains):
            return adapter

    return GENERIC_MARKETPLACE
