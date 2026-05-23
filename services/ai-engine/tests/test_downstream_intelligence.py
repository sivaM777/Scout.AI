import asyncio
import unittest
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock, patch

from app.models.schemas import ProductIdentity
from app.services.price_intelligence import build_pricing_insight
from app.services.price_store import PriceSnapshotStore
from app.services.review_sources import RedditPost, YouTubeReview, gather_review_signals


def _price_html(amount: int, currency: str = "INR") -> str:
    return f"""
<html>
  <head>
    <meta property="product:price:amount" content="{amount}" />
    <meta property="product:price:currency" content="{currency}" />
    <script type="application/ld+json">
      {{
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "Samsung Galaxy A55 5G",
        "offers": {{
          "@type": "Offer",
          "price": "{amount}",
          "priceCurrency": "{currency}"
        }}
      }}
    </script>
  </head>
  <body>
    <div class="price">Rs. {amount:,}</div>
  </body>
</html>
"""


AMAZON_PRICE_HTML = """
<html>
  <body>
    <div id="corePriceDisplay_desktop_feature_div">
      <span class="a-price">
        <span class="a-offscreen">₹69,999.00</span>
      </span>
    </div>
  </body>
</html>
"""


FLIPKART_PRICE_HTML = """
<html>
  <body>
    <div class="Nx9bqj">₹52,499</div>
  </body>
</html>
"""


RELIANCE_PRICE_HTML = """
<html>
  <body>
    <div class="add-to-card-container__product-price">₹58,990.00</div>
    <span class="product-marked-price">₹59,900.00</span>
  </body>
</html>
"""


class DownstreamIntelligenceTests(unittest.TestCase):
    def test_pricing_uses_live_html_price_and_persists_history(self) -> None:
        product = ProductIdentity(
            marketplace="Amazon",
            name="Samsung Galaxy A55 5G 128GB",
            brand="Samsung",
            category="electronics",
            image="https://images.example.com/galaxy-a55.jpg",
        )

        with TemporaryDirectory() as temp_dir:
            store = PriceSnapshotStore(Path(temp_dir) / "price-history.sqlite3")
            url = "https://www.amazon.in/Samsung-Galaxy-A55-5G/dp/B0TEST1234"

            first = build_pricing_insight(
                url,
                product,
                html=_price_html(52999),
                snapshot_store=store,
                observed_at=datetime(2026, 5, 20, 9, 30, tzinfo=UTC),
            )
            second = build_pricing_insight(
                url,
                product,
                html=_price_html(49999),
                snapshot_store=store,
                observed_at=datetime(2026, 5, 23, 18, 45, tzinfo=UTC),
            )

        self.assertEqual(52999.0, first.current_price)
        self.assertEqual(49999.0, second.current_price)
        self.assertEqual("INR", second.currency)
        self.assertEqual(2, len(second.history))
        self.assertEqual("Now", second.history[-1].label)
        self.assertEqual(49999.0, second.history[-1].value)
        self.assertEqual(51499.0, second.average_price)
        self.assertEqual(49999.0, second.lowest_price)

    def test_marketplace_specific_price_selectors_extract_live_prices(self) -> None:
        cases = [
            (
                "https://www.amazon.in/Apple-iPhone-15-128-GB-Black/dp/B0CHX1W1XY",
                ProductIdentity(
                    marketplace="Amazon",
                    name="Apple iPhone 15 128GB Black",
                    brand="Apple",
                    category="electronics",
                    image="https://images.example.com/iphone15.jpg",
                ),
                AMAZON_PRICE_HTML,
                69999.0,
            ),
            (
                "https://www.flipkart.com/samsung-galaxy-s23-5g-cream-128-gb/p/itm1234567890?pid=MOBGQ9M92MZP7K7S",
                ProductIdentity(
                    marketplace="Flipkart",
                    name="Samsung Galaxy S23 5G Cream 128GB",
                    brand="Samsung",
                    category="electronics",
                    image="https://images.example.com/galaxy-s23.jpg",
                ),
                FLIPKART_PRICE_HTML,
                52499.0,
            ),
            (
                "https://www.reliancedigital.in/product/apple-iphone-15-128gb-black-lmiqm4-7533780",
                ProductIdentity(
                    marketplace="Reliance Digital",
                    name="Apple iPhone 15 128GB Black",
                    brand="Apple",
                    category="electronics",
                    image="https://images.example.com/iphone15.jpg",
                ),
                RELIANCE_PRICE_HTML,
                58990.0,
            ),
        ]

        for url, product, html, expected_price in cases:
            with self.subTest(url=url):
                pricing = build_pricing_insight(url, product, html=html)
                self.assertEqual("live", pricing.price_source)
                self.assertEqual(expected_price, pricing.current_price)

    @patch("app.services.review_sources._search_youtube_reviews", new_callable=AsyncMock)
    @patch("app.services.review_sources._fetch_reddit_posts", new_callable=AsyncMock)
    def test_review_signals_include_live_reddit_and_youtube_summaries(
        self,
        mock_reddit: AsyncMock,
        mock_youtube: AsyncMock,
    ) -> None:
        product_url = "https://www.flipkart.com/samsung-galaxy-a55-5g/p/itmexample"
        product = ProductIdentity(
            marketplace="Flipkart",
            name="Samsung Galaxy A55 5G 128GB",
            brand="Samsung",
            category="electronics",
            image="https://images.example.com/galaxy-a55.jpg",
        )

        mock_reddit.return_value = [
            RedditPost(
                title="Galaxy A55 owners report solid battery but average night camera",
                url="https://www.reddit.com/r/Android/comments/example1",
                body="Most people like the battery life, but several mention camera processing and heating during gaming.",
                score=192,
                comment_count=64,
            )
        ]
        mock_youtube.return_value = [
            YouTubeReview(
                video_id="abc123",
                title="Samsung Galaxy A55 Review After 2 Weeks",
                url="https://www.youtube.com/watch?v=abc123",
                transcript="Battery life is strong, the display looks premium, but gaming heat and slow charging are still worth noting.",
            )
        ]

        sources = asyncio.run(gather_review_signals(product, product_url=product_url))

        self.assertEqual(6, len(sources))
        self.assertEqual("reddit", sources[0].source_type)
        self.assertEqual("https://www.reddit.com/r/Android/comments/example1", str(sources[0].url))
        self.assertIn("battery", sources[0].summary.lower())
        self.assertEqual("youtube", sources[1].source_type)
        self.assertEqual("https://www.youtube.com/watch?v=abc123", str(sources[1].url))
        self.assertIn("display looks premium", sources[1].summary.lower())
        self.assertIn("battery", str(sources[3].url))
        self.assertEqual(product_url, str(sources[-1].url))


if __name__ == "__main__":
    unittest.main()
