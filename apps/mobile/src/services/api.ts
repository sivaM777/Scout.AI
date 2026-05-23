import { analysisReportSchema, watchlistItemSchema, type AnalysisReport, type AnalyzeLinkRequest, type WatchlistItem } from "@scout/shared";
import { mockAnalysisReport, mockWatchlist } from "../data/mock-analysis";
import { API_BASE_URL } from "../config/runtime";

function inferMarketplace(url: string): string {
  try {
    const hostname = new URL(url).hostname.toLowerCase();

    if (hostname.includes("amazon")) {
      return "Amazon";
    }
    if (hostname.includes("flipkart")) {
      return "Flipkart";
    }
    if (hostname.includes("ajio")) {
      return "Ajio";
    }
    if (hostname.includes("myntra")) {
      return "Myntra";
    }
  } catch {
    return "Online Store";
  }

  return "Online Store";
}

function inferName(url: string): string {
  try {
    const slug = new URL(url).pathname.split("/").filter(Boolean).at(-1) ?? "product-research";
    return slug.replace(/[-_]+/g, " ").replace(/\b[a-z0-9]{8,}\b/gi, " ").trim() || "Product Research";
  } catch {
    return "Product Research";
  }
}

export async function analyzeProductLink(payload: AnalyzeLinkRequest): Promise<AnalysisReport> {
  try {
    const response = await fetch(`${API_BASE_URL}/v1/analysis`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Gateway failed with status ${response.status}`);
    }

    const data = await response.json();
    return analysisReportSchema.parse(data.report);
  } catch {
    return {
      ...mockAnalysisReport,
      id: `demo-${Date.now()}`,
      productUrl: payload.url,
      marketplace: inferMarketplace(payload.url),
      productName: inferName(payload.url),
      generatedAt: new Date().toISOString(),
    };
  }
}

export async function fetchHistory(): Promise<AnalysisReport[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/v1/history`);
    const data = await response.json();
    return (data.items as unknown[]).map((item) => analysisReportSchema.parse(item));
  } catch {
    return [mockAnalysisReport];
  }
}

export async function fetchWatchlist(): Promise<WatchlistItem[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/v1/watchlist`);
    const data = await response.json();
    return (data.items as unknown[]).map((item) => watchlistItemSchema.parse(item));
  } catch {
    return mockWatchlist;
  }
}

type CreateWatchlistInput = {
  productName: string;
  productUrl: string;
  currentPrice: number;
  currency: string;
  targetPrice?: number;
  note?: string;
};

export async function createWatchlistItem(input: CreateWatchlistInput): Promise<WatchlistItem> {
  try {
    const response = await fetch(`${API_BASE_URL}/v1/watchlist`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(input),
    });

    const data = await response.json();
    return watchlistItemSchema.parse(data.item);
  } catch {
    return {
      id: `local-${Date.now()}`,
      addedAt: new Date().toISOString(),
      ...input,
    };
  }
}
