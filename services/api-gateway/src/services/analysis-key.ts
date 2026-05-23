import { createHash } from "node:crypto";
import type { AnalyzeLinkRequest } from "@scout/shared";

export function normalizeProductUrl(rawUrl: string): string {
  const url = new URL(rawUrl);
  url.hash = "";

  const params = [...url.searchParams.entries()]
    .sort(([leftKey], [rightKey]) => leftKey.localeCompare(rightKey))
    .filter(([key]) => !key.toLowerCase().startsWith("utm"));

  url.search = "";
  for (const [key, value] of params) {
    url.searchParams.append(key, value);
  }

  return url.toString();
}

function normalizePreferences(payload: AnalyzeLinkRequest): string {
  if (!payload.preferences) {
    return "default";
  }

  const normalized = {
    ...payload.preferences,
    selectedMarketplaces: [...payload.preferences.selectedMarketplaces].sort(),
  };

  return JSON.stringify(normalized);
}

export function buildAnalysisCacheKey(payload: AnalyzeLinkRequest): string {
  const normalizedUrl = normalizeProductUrl(payload.url);
  const cacheBasis = `${normalizedUrl}|${normalizePreferences(payload)}`;
  return `analysis:${createHash("sha1").update(cacheBasis).digest("hex")}`;
}
