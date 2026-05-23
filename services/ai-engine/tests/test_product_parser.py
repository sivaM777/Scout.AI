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


if __name__ == "__main__":
    unittest.main()
