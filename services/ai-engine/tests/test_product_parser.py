import unittest

from app.services.product_parser import parse_product_identity


URL_CASES = [
    {
        "url": "https://www.amazon.in/Apple-iPhone-15-128-GB-Black/dp/B0CHX1W1XY",
        "marketplace": "Amazon",
        "brand": "Apple",
        "category": "electronics",
        "name_parts": ("iPhone", "15"),
    },
    {
        "url": "https://www.flipkart.com/samsung-galaxy-s23-5g-cream-128-gb/p/itm1234567890?pid=MOBGQ9M92MZP7K7S",
        "marketplace": "Flipkart",
        "brand": "Samsung",
        "category": "electronics",
        "name_parts": ("Samsung", "S23"),
    },
    {
        "url": "https://www.ajio.com/nike-air-max-alpha-trainer-5-shoes/p/469537117_black",
        "marketplace": "Ajio",
        "brand": "Nike",
        "category": "fashion",
        "name_parts": ("Nike", "Shoes"),
    },
    {
        "url": "https://www.myntra.com/tshirts/hm/hm-men-regular-fit-cotton-t-shirt/30123456/buy",
        "marketplace": "Myntra",
        "brand": "H&M",
        "category": "fashion",
        "name_parts": ("Cotton", "Shirt"),
    },
    {
        "url": "https://www.nykaa.com/maybelline-new-york-fit-me-matte-poreless-foundation/p/183373",
        "marketplace": "Nykaa",
        "brand": "Maybelline",
        "category": "beauty",
        "name_parts": ("Maybelline", "Foundation"),
    },
    {
        "url": "https://www.tatacliq.com/apple-iphone-15-128gb-black/p-mp000000020854859",
        "marketplace": "Tata CLiQ",
        "brand": "Apple",
        "category": "electronics",
        "name_parts": ("iPhone", "128GB"),
    },
    {
        "url": "https://www.meesho.com/boat-rockerz-255-pro-plus-neckband/p/6c5r9k",
        "marketplace": "Meesho",
        "brand": "boAt",
        "category": "electronics",
        "name_parts": ("Rockerz", "Neckband"),
    },
    {
        "url": "https://www.croma.com/apple-iphone-15-128gb-black/p/300123456",
        "marketplace": "Croma",
        "brand": "Apple",
        "category": "electronics",
        "name_parts": ("Apple", "128GB"),
    },
    {
        "url": "https://www.reliancedigital.in/apple-iphone-15-128-gb-black/p/493839489",
        "marketplace": "Reliance Digital",
        "brand": "Apple",
        "category": "electronics",
        "name_parts": ("iPhone", "128"),
    },
    {
        "url": "https://www.vijaysales.com/apple-iphone-15-128gb-black/234567",
        "marketplace": "Vijay Sales",
        "brand": "Apple",
        "category": "electronics",
        "name_parts": ("iPhone", "Black"),
    },
    {
        "url": "https://www.snapdeal.com/product/boat-rockerz-255-pro-plus/6917529689452049461",
        "marketplace": "Snapdeal",
        "brand": "boAt",
        "category": "electronics",
        "name_parts": ("Rockerz", "255"),
    },
    {
        "url": "https://www.jiomart.com/p/groceries/amul-taaza-toned-fresh-milk-500-ml/590003000",
        "marketplace": "JioMart",
        "brand": "Amul",
        "category": "grocery",
        "name_parts": ("Milk", "500ML"),
    },
    {
        "url": "https://www.firstcry.com/babyhug/babyhug-cotton-t-shirt-with-shorts-blue/12345678/product-detail",
        "marketplace": "FirstCry",
        "brand": "Babyhug",
        "category": "kids",
        "name_parts": ("Cotton", "Shorts"),
    },
    {
        "url": "https://www.zara.com/in/en/textured-knit-polo-shirt-p03920520.html?v1=364239001",
        "marketplace": "Zara",
        "brand": "Zara",
        "category": "fashion",
        "name_parts": ("Polo", "Shirt"),
    },
    {
        "url": "https://www.bestbuy.com/site/apple-airpods-pro-2-white/6447382.p?skuId=6447382",
        "marketplace": "Best Buy",
        "brand": "Apple",
        "category": "electronics",
        "name_parts": ("Airpods", "Pro"),
    },
]

HM_HTML = """
<html>
  <head>
    <meta property="og:title" content="Rib-knit top" />
    <meta property="og:image" content="https://image.hm.com/product.jpg" />
    <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "Rib-knit top",
        "brand": { "@type": "Brand", "name": "H&M" },
        "image": ["https://image.hm.com/product.jpg"],
        "category": "fashion"
      }
    </script>
  </head>
  <body></body>
</html>
"""

FLIPKART_GENERIC_HTML = """
<html>
  <head>
    <title>Online at Best Price in India | All Categories | Flipkart.com</title>
    <meta property="og:title" content="Online at Best Price in India | All Categories" />
  </head>
  <body></body>
</html>
"""

AMAZON_GENERIC_HTML = """
<html>
  <head>
    <title>Amazon.in</title>
    <meta property="og:title" content="Amazon.in" />
  </head>
  <body></body>
</html>
"""

CROMA_GENERIC_HTML = """
<html>
  <head>
    <title>Croma Electronics | Online Electronics Shopping</title>
    <meta property="og:title" content="Croma Electronics Online Electronics Shopping" />
  </head>
  <body></body>
</html>
"""

MYNTRA_MAINTENANCE_HTML = """
<html>
  <head>
    <title>Maintenance</title>
    <meta property="og:title" content="Maintenance" />
  </head>
  <body></body>
</html>
"""
AMAZON_DETAIL_HTML = """
<html>
  <head>
    <title>Apple iPhone 15 (128 GB) - Black : Amazon.in</title>
  </head>
  <body>
    <span id="productTitle">Apple iPhone 15 (128 GB) - Black</span>
    <a id="bylineInfo">Visit the Apple Store</a>
    <img id="landingImage" src="https://images.example.com/iphone15.jpg" />
  </body>
</html>
"""

RELIANCE_DETAIL_HTML = """
<html>
  <head>
    <title>Apple iPhone 15 128 GB Black | Reliance Digital</title>
  </head>
  <body>
    <h1 class="pdp__title">Apple iPhone 15 128 GB Black</h1>
    <img class="pdp__image" src="https://images.example.com/reliance-iphone15.jpg" />
  </body>
</html>
"""


class ProductParserTests(unittest.TestCase):
    def test_marketplace_specific_url_extraction(self) -> None:
        for case in URL_CASES:
            with self.subTest(url=case["url"]):
                product = parse_product_identity(case["url"])
                self.assertEqual(product.marketplace, case["marketplace"])
                self.assertEqual(product.brand, case["brand"])
                self.assertEqual(product.category, case["category"])
                for part in case["name_parts"]:
                    self.assertIn(part, product.name)

    def test_html_metadata_enriches_hm_product(self) -> None:
        product = parse_product_identity(
            "https://www2.hm.com/en_in/productpage.1234567001.html",
            html=HM_HTML,
        )

        self.assertEqual(product.marketplace, "H&M")
        self.assertEqual(product.brand, "H&M")
        self.assertEqual(product.category, "fashion")
        self.assertEqual(product.name, "Rib Knit Top")
        self.assertEqual(str(product.image), "https://image.hm.com/product.jpg")

    def test_generic_marketplace_metadata_does_not_override_url_identity(self) -> None:
        cases = [
            {
                "url": "https://www.flipkart.com/samsung-galaxy-s23-5g-cream-128-gb/p/itm1234567890?pid=MOBGQ9M92MZP7K7S",
                "html": FLIPKART_GENERIC_HTML,
                "marketplace": "Flipkart",
                "brand": "Samsung",
                "name_parts": ("Galaxy", "S23"),
            },
            {
                "url": "https://www.amazon.in/Apple-iPhone-15-128-GB-Black/dp/B0CHX1W1XY",
                "html": AMAZON_GENERIC_HTML,
                "marketplace": "Amazon",
                "brand": "Apple",
                "name_parts": ("iPhone", "15"),
            },
            {
                "url": "https://www.croma.com/apple-iphone-15-128gb-black/p/300123456",
                "html": CROMA_GENERIC_HTML,
                "marketplace": "Croma",
                "brand": "Apple",
                "name_parts": ("iPhone", "128GB"),
            },
            {
                "url": "https://www.myntra.com/tshirts/hm/hm-men-regular-fit-cotton-t-shirt/30123456/buy",
                "html": MYNTRA_MAINTENANCE_HTML,
                "marketplace": "Myntra",
                "brand": "H&M",
                "name_parts": ("Cotton", "Shirt"),
            },
        ]

        for case in cases:
            with self.subTest(url=case["url"]):
                product = parse_product_identity(case["url"], html=case["html"])
                self.assertEqual(product.marketplace, case["marketplace"])
                self.assertEqual(product.brand, case["brand"])
                for part in case["name_parts"]:
                    self.assertIn(part, product.name)

    def test_hm_url_fallback_produces_specific_name(self) -> None:
        product = parse_product_identity("https://www2.hm.com/en_in/productpage.1234567001.html")

        self.assertEqual(product.marketplace, "H&M")
        self.assertEqual(product.brand, "H&M")
        self.assertEqual(product.category, "fashion")
        self.assertIn("Fashion", product.name)
        self.assertIn("Piece", product.name)

    def test_site_specific_html_selectors_enrich_priority_marketplaces(self) -> None:
        amazon = parse_product_identity(
            "https://www.amazon.in/Apple-iPhone-15-128-GB-Black/dp/B0CHX1W1XY",
            html=AMAZON_DETAIL_HTML,
        )
        reliance = parse_product_identity(
            "https://www.reliancedigital.in/apple-iphone-15-128-gb-black/p/493839489",
            html=RELIANCE_DETAIL_HTML,
        )

        self.assertEqual("Apple", amazon.brand)
        self.assertEqual("Apple iPhone 15 128GB Black", amazon.name)
        self.assertEqual("https://images.example.com/iphone15.jpg", str(amazon.image))

        self.assertEqual("Reliance Digital", reliance.marketplace)
        self.assertEqual("Apple", reliance.brand)
        self.assertIn("iPhone 15", reliance.name)
        self.assertEqual("https://images.example.com/reliance-iphone15.jpg", str(reliance.image))


if __name__ == "__main__":
    unittest.main()
