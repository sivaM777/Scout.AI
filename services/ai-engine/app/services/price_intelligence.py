from hashlib import sha1

from app.models.schemas import PricePoint, PricingInsight


def _seed_from_url(url: str) -> int:
    return int(sha1(url.encode("utf-8")).hexdigest()[:8], 16)


def _price_band(seed: int) -> tuple[float, str]:
    bands = [
        (899.0, "INR"),
        (1499.0, "INR"),
        (3499.0, "INR"),
        (7999.0, "INR"),
        (19999.0, "INR"),
    ]
    return bands[seed % len(bands)]


def build_pricing_insight(url: str) -> PricingInsight:
    seed = _seed_from_url(url)
    base_price, currency = _price_band(seed)
    current_price = base_price + (seed % 700)
    average_price = current_price + 420
    lowest_price = max(current_price - 640, base_price * 0.75)
    target_price = round((average_price + lowest_price) / 2, 2)
    is_good_deal = current_price <= target_price

    history = [
        PricePoint(label="Jan", value=round(average_price + 220, 2)),
        PricePoint(label="Feb", value=round(average_price + 80, 2)),
        PricePoint(label="Mar", value=round(current_price + 180, 2)),
        PricePoint(label="Apr", value=round(current_price + 40, 2)),
        PricePoint(label="Now", value=round(current_price, 2)),
    ]

    return PricingInsight(
        currentPrice=round(current_price, 2),
        averagePrice=round(average_price, 2),
        lowestPrice=round(lowest_price, 2),
        recommendedTargetPrice=round(target_price, 2),
        currency=currency,
        isGoodDeal=is_good_deal,
        history=history,
    )
