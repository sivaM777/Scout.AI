import type { AnalysisReport, WatchlistItem } from "@scout/shared";

export const mockAnalysisReport: AnalysisReport = {
  id: "demo-1",
  productUrl: "https://www.ajio.com/sample-product/p/123456",
  marketplace: "Ajio",
  productName: "Relaxed Fit Linen Blend Dress",
  productBrand: "Ajio",
  productImage: "https://placehold.co/600x600/png",
  productCategory: "Fashion",
  overallScore: 81,
  confidence: 84,
  verdict: "buy",
  oneLineSummary: "A stylish value pick that feels worth buying when the fit works for your wardrobe.",
  verdictReason:
    "Community-style feedback and editorial fashion signals suggest the material and silhouette are liked, while shoppers still need to double-check fit expectations and the current discount level.",
  pros: [
    "Looks premium for the current price bracket.",
    "Comfort and easy styling are repeatedly mentioned in review-style commentary.",
    "Works well as an everyday wardrobe piece.",
  ],
  cons: [
    "Fit can vary depending on body shape and expected drape.",
    "Discount depth changes how strong the value feels.",
    "Fabric finish may not satisfy shoppers expecting a true premium label.",
  ],
  communityPulse: "Most shoppers would shortlist it, but many would still wait for the right size and a sharper price drop.",
  sources: [
    {
      id: "source-1",
      sourceType: "reddit",
      title: "Owner-style fashion discussion",
      url: "https://www.reddit.com/search/?q=linen+dress+review",
      sentiment: "mixed",
      summary: "Useful fit notes and realistic comments about how the fabric behaves after multiple wears.",
      trustLabel: "Community signal",
    },
    {
      id: "source-2",
      sourceType: "youtube",
      title: "Wardrobe review roundup",
      url: "https://www.youtube.com/results?search_query=linen+dress+review",
      sentiment: "positive",
      summary: "Video reviewers like the styling flexibility and generally call it a good everyday piece.",
      trustLabel: "Video signal",
    },
    {
      id: "source-3",
      sourceType: "blog",
      title: "Editorial fashion review",
      url: "https://www.google.com/search?q=linen+dress+review+blog",
      sentiment: "mixed",
      summary: "Blog coverage adds context on silhouette, wash care, and who should size up or pass.",
      trustLabel: "Editorial signal",
    },
  ],
  pricing: {
    currentPrice: 1899,
    averagePrice: 2249,
    lowestPrice: 1699,
    recommendedTargetPrice: 1924,
    currency: "INR",
    isGoodDeal: true,
    history: [
      { label: "Jan", value: 2399 },
      { label: "Feb", value: 2299 },
      { label: "Mar", value: 2099 },
      { label: "Apr", value: 1949 },
      { label: "Now", value: 1899 },
    ],
  },
  alternatives: [
    {
      id: "alt-1",
      name: "Minimal Cotton Day Dress",
      reason: "Safer fit profile for most shoppers.",
      estimatedPrice: 1799,
      verdict: "buy",
    },
    {
      id: "alt-2",
      name: "Premium Resort Midi Dress",
      reason: "Better fabric finish if you can stretch the budget.",
      estimatedPrice: 2599,
      verdict: "wait",
    },
  ],
  generatedAt: "2026-05-23T10:00:00Z",
};

export const mockWatchlist: WatchlistItem[] = [
  {
    id: "watch-1",
    productName: "Relaxed Fit Linen Blend Dress",
    productUrl: "https://www.ajio.com/sample-product/p/123456",
    targetPrice: 1799,
    currentPrice: 1899,
    currency: "INR",
    note: "Buy if it drops below 1800.",
    addedAt: "2026-05-20T08:00:00Z",
  },
];
