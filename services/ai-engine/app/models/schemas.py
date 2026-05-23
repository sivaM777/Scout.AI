from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


Verdict = Literal["buy", "wait", "skip"]
Sentiment = Literal["positive", "mixed", "negative"]
SourceType = Literal["reddit", "youtube", "blog", "editorial", "community"]


class AnalyzeLinkPayload(BaseModel):
    url: HttpUrl
    source_app: str | None = Field(default=None, alias="sourceApp")
    user_note: str | None = Field(default=None, alias="userNote")

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

    model_config = {
        "populate_by_name": True,
    }


class PricePoint(BaseModel):
    label: str
    value: float


class PricingInsight(BaseModel):
    current_price: float = Field(alias="currentPrice")
    average_price: float = Field(alias="averagePrice")
    lowest_price: float = Field(alias="lowestPrice")
    recommended_target_price: float = Field(alias="recommendedTargetPrice")
    currency: str
    is_good_deal: bool = Field(alias="isGoodDeal")
    history: list[PricePoint]

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
