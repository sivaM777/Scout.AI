import {
  analysisReportSchema,
  defaultResearchSettings,
  watchlistItemSchema,
  type AnalysisReport,
  type AnalyzeLinkRequest,
  type WatchlistItem,
} from "@scout/shared";
import { mockWatchlist } from "../data/mock-analysis";
import { API_BASE_URL } from "../config/runtime";

export async function analyzeProductLink(payload: AnalyzeLinkRequest): Promise<AnalysisReport> {
  const requestPayload: AnalyzeLinkRequest = payload.preferences
    ? {
        ...payload,
        preferences: {
          ...defaultResearchSettings,
          ...payload.preferences,
        },
      }
    : payload;

  const response = await fetch(`${API_BASE_URL}/v1/analysis`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(requestPayload),
  });

  if (!response.ok) {
    throw new Error(`Gateway failed with status ${response.status}`);
  }

  const data = await response.json();
  return analysisReportSchema.parse(data.report);
}

export async function fetchHistory(): Promise<AnalysisReport[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/v1/history`);
    const data = await response.json();
    return (data.items as unknown[]).map((item) => analysisReportSchema.parse(item));
  } catch {
    return [];
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
