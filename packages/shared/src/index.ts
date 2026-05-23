import { z } from "zod";

export const verdictSchema = z.enum(["buy", "wait", "skip"]);
export const marketplaceSlugSchema = z.enum([
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
]);
export const dealPreferenceSchema = z.enum(["aggressive", "balanced", "conservative"]);
export const priceStatusSchema = z.enum(["current", "cheaper", "same", "higher", "unavailable"]);
export const pricingSourceSchema = z.enum(["live", "historical", "estimated"]);

export const supportedMarketplaceOptions = [
  { slug: "amazon", label: "Amazon" },
  { slug: "flipkart", label: "Flipkart" },
  { slug: "ajio", label: "Ajio" },
  { slug: "myntra", label: "Myntra" },
  { slug: "nykaa", label: "Nykaa" },
  { slug: "tatacliq", label: "Tata CLiQ" },
  { slug: "meesho", label: "Meesho" },
  { slug: "croma", label: "Croma" },
  { slug: "reliance-digital", label: "Reliance Digital" },
  { slug: "vijay-sales", label: "Vijay Sales" },
  { slug: "snapdeal", label: "Snapdeal" },
  { slug: "jiomart", label: "JioMart" },
  { slug: "firstcry", label: "FirstCry" },
  { slug: "hm", label: "H&M" },
  { slug: "zara", label: "Zara" },
  { slug: "best-buy", label: "Best Buy" },
] as const;

export const researchSettingsSchema = z.object({
  compareAcrossMarketplaces: z.boolean(),
  selectedMarketplaces: z.array(marketplaceSlugSchema).min(1),
  includeReddit: z.boolean(),
  includeYouTube: z.boolean(),
  includeEditorial: z.boolean(),
  dealPreference: dealPreferenceSchema,
  showPriceDeltaPercent: z.boolean(),
});

export const sourceEvidenceSchema = z.object({
  id: z.string(),
  sourceType: z.enum(["reddit", "youtube", "blog", "editorial", "community"]),
  title: z.string(),
  url: z.string().url(),
  sentiment: z.enum(["positive", "mixed", "negative"]),
  summary: z.string(),
  trustLabel: z.string(),
  domain: z.string().optional(),
  evidenceCount: z.number().int().nonnegative().optional(),
  snippet: z.string().optional(),
});

export const pricePointSchema = z.object({
  label: z.string(),
  value: z.number(),
});

export const marketplacePriceSchema = z.object({
  marketplaceSlug: marketplaceSlugSchema,
  marketplaceLabel: z.string(),
  productName: z.string(),
  productUrl: z.string().url().optional(),
  currency: z.string(),
  currentPrice: z.number().nullable(),
  availability: z.enum(["available", "unavailable"]),
  differenceAmount: z.number().nullable(),
  differencePercent: z.number().nullable(),
  matchScore: z.number().min(0).max(1),
  priceStatus: priceStatusSchema,
  isOriginalListing: z.boolean(),
  note: z.string().optional(),
});

export const alternativeSchema = z.object({
  id: z.string(),
  name: z.string(),
  reason: z.string(),
  estimatedPrice: z.number(),
  verdict: verdictSchema,
});

export const pricingInsightSchema = z.object({
  currentPrice: z.number(),
  averagePrice: z.number(),
  lowestPrice: z.number(),
  recommendedTargetPrice: z.number(),
  currency: z.string(),
  isGoodDeal: z.boolean(),
  priceSource: pricingSourceSchema,
  history: z.array(pricePointSchema),
  marketplacePrices: z.array(marketplacePriceSchema),
});

export const analysisReportSchema = z.object({
  id: z.string(),
  productUrl: z.string().url(),
  marketplace: z.string(),
  productName: z.string(),
  productBrand: z.string(),
  productImage: z.string().url(),
  productCategory: z.string(),
  overallScore: z.number().min(0).max(100),
  confidence: z.number().min(0).max(100),
  verdict: verdictSchema,
  oneLineSummary: z.string(),
  verdictReason: z.string(),
  pros: z.array(z.string()),
  cons: z.array(z.string()),
  communityPulse: z.string(),
  sources: z.array(sourceEvidenceSchema),
  pricing: pricingInsightSchema,
  alternatives: z.array(alternativeSchema),
  generatedAt: z.string(),
});

export const analyzeLinkRequestSchema = z.object({
  url: z.string().url(),
  sourceApp: z.string().optional(),
  userNote: z.string().max(280).optional(),
  preferences: researchSettingsSchema.optional(),
});

export const watchlistItemSchema = z.object({
  id: z.string(),
  productName: z.string(),
  productUrl: z.string().url(),
  targetPrice: z.number().optional(),
  currentPrice: z.number(),
  currency: z.string(),
  note: z.string().optional(),
  addedAt: z.string(),
});

export type Verdict = z.infer<typeof verdictSchema>;
export type MarketplaceSlug = z.infer<typeof marketplaceSlugSchema>;
export type DealPreference = z.infer<typeof dealPreferenceSchema>;
export type PriceStatus = z.infer<typeof priceStatusSchema>;
export type PricingSource = z.infer<typeof pricingSourceSchema>;
export type ResearchSettings = z.infer<typeof researchSettingsSchema>;
export type SourceEvidence = z.infer<typeof sourceEvidenceSchema>;
export type PricePoint = z.infer<typeof pricePointSchema>;
export type MarketplacePrice = z.infer<typeof marketplacePriceSchema>;
export type AlternativeProduct = z.infer<typeof alternativeSchema>;
export type PricingInsight = z.infer<typeof pricingInsightSchema>;
export type AnalysisReport = z.infer<typeof analysisReportSchema>;
export type AnalyzeLinkRequest = z.infer<typeof analyzeLinkRequestSchema>;
export type WatchlistItem = z.infer<typeof watchlistItemSchema>;

export const defaultResearchSettings: ResearchSettings = {
  compareAcrossMarketplaces: true,
  selectedMarketplaces: supportedMarketplaceOptions.map((option) => option.slug),
  includeReddit: true,
  includeYouTube: true,
  includeEditorial: true,
  dealPreference: "balanced",
  showPriceDeltaPercent: true,
};
