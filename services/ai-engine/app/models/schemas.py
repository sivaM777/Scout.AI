from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


Verdict = Literal["buy", "wait", "skip"]
Sentiment = Literal["positive", "mixed", "negative"]
SourceType = Literal["reddit", "youtube", "blog", "editorial", "community"]
MarketplaceSlug = Literal[
    "generic",
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
]
DealPreference = Literal["aggressive", "balanced", "conservative"]
PriceStatus = Literal["current", "cheaper", "same", "higher", "unavailable"]
PricingSource = Literal["live", "historical", "estimated"]


class AnalyzeLinkPayload(BaseModel):
    url: HttpUrl
    source_app: str | None = Field(default=None, alias="sourceApp")
    user_note: str | None = Field(default=None, alias="userNote")
    preferences: "ResearchPreferences | None" = None

    model_config = {
        "populate_by_name": True,
    }


class ProductIdentity(BaseModel):
    marketplace: str
    name: str
    brand: str
    category: str
    image: HttpUrl


class SourceEvidence(BaseModel):
    id: str
    source_type: SourceType = Field(alias="sourceType")
    title: str
    url: HttpUrl
    sentiment: Sentiment
    summary: str
    trust_label: str = Field(alias="trustLabel")
    domain: str | None = None
    evidence_count: int | None = Field(default=None, alias="evidenceCount")
    snippet: str | None = None

    model_config = {
        "populate_by_name": True,
    }


class PricePoint(BaseModel):
    label: str
    value: float


class MarketplacePrice(BaseModel):
    marketplace_slug: MarketplaceSlug = Field(alias="marketplaceSlug")
    marketplace_label: str = Field(alias="marketplaceLabel")
    product_name: str = Field(alias="productName")
    product_url: HttpUrl | None = Field(default=None, alias="productUrl")
    currency: str
    current_price: float | None = Field(alias="currentPrice")
    availability: Literal["available", "unavailable"]
    difference_amount: float | None = Field(alias="differenceAmount")
    difference_percent: float | None = Field(alias="differencePercent")
    match_score: float = Field(alias="matchScore")
    price_status: PriceStatus = Field(alias="priceStatus")
    is_original_listing: bool = Field(alias="isOriginalListing")
    note: str | None = None

    model_config = {
        "populate_by_name": True,
    }


class PricingInsight(BaseModel):
    current_price: float = Field(alias="currentPrice")
    average_price: float = Field(alias="averagePrice")
    lowest_price: float = Field(alias="lowestPrice")
    recommended_target_price: float = Field(alias="recommendedTargetPrice")
    currency: str
    is_good_deal: bool = Field(alias="isGoodDeal")
    price_source: PricingSource = Field(alias="priceSource")
    history: list[PricePoint]
    marketplace_prices: list[MarketplacePrice] = Field(alias="marketplacePrices")

    model_config = {
        "populate_by_name": True,
    }


class AlternativeProduct(BaseModel):
    id: str
    name: str
    reason: str
    estimated_price: float = Field(alias="estimatedPrice")
    verdict: Verdict

    model_config = {
        "populate_by_name": True,
    }


class ResearchPreferences(BaseModel):
    compare_across_marketplaces: bool = Field(alias="compareAcrossMarketplaces")
    selected_marketplaces: list[MarketplaceSlug] = Field(alias="selectedMarketplaces")
    include_reddit: bool = Field(alias="includeReddit")
    include_youtube: bool = Field(alias="includeYouTube")
    include_editorial: bool = Field(alias="includeEditorial")
    deal_preference: DealPreference = Field(alias="dealPreference")
    show_price_delta_percent: bool = Field(alias="showPriceDeltaPercent")

    model_config = {
        "populate_by_name": True,
    }


class AnalysisReport(BaseModel):
    id: str
    product_url: HttpUrl = Field(alias="productUrl")
    marketplace: str
    product_name: str = Field(alias="productName")
    product_brand: str = Field(alias="productBrand")
    product_image: HttpUrl = Field(alias="productImage")
    product_category: str = Field(alias="productCategory")
    overall_score: int = Field(alias="overallScore")
    confidence: int
    verdict: Verdict
    one_line_summary: str = Field(alias="oneLineSummary")
    verdict_reason: str = Field(alias="verdictReason")
    pros: list[str]
    cons: list[str]
    community_pulse: str = Field(alias="communityPulse")
    sources: list[SourceEvidence]
    pricing: PricingInsight
    alternatives: list[AlternativeProduct]
    generated_at: str = Field(alias="generatedAt")

    model_config = {
        "populate_by_name": True,
    }


AnalyzeLinkPayload.model_rebuild()
