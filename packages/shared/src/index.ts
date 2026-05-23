import { z } from "zod";

export const verdictSchema = z.enum(["buy", "wait", "skip"]);

export const sourceEvidenceSchema = z.object({
  id: z.string(),
  sourceType: z.enum(["reddit", "youtube", "blog", "editorial", "community"]),
  title: z.string(),
  url: z.string().url(),
  sentiment: z.enum(["positive", "mixed", "negative"]),
  summary: z.string(),
  trustLabel: z.string(),
});

export const pricePointSchema = z.object({
  label: z.string(),
  value: z.number(),
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
  history: z.array(pricePointSchema),
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
export type SourceEvidence = z.infer<typeof sourceEvidenceSchema>;
export type PricePoint = z.infer<typeof pricePointSchema>;
export type AlternativeProduct = z.infer<typeof alternativeSchema>;
export type PricingInsight = z.infer<typeof pricingInsightSchema>;
export type AnalysisReport = z.infer<typeof analysisReportSchema>;
export type AnalyzeLinkRequest = z.infer<typeof analyzeLinkRequestSchema>;
export type WatchlistItem = z.infer<typeof watchlistItemSchema>;
