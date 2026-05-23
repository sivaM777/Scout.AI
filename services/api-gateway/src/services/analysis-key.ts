import { createHash } from "node:crypto";

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

export function buildAnalysisCacheKey(rawUrl: string): string {
  const normalizedUrl = normalizeProductUrl(rawUrl);
  return `analysis:${createHash("sha1").update(normalizedUrl).digest("hex")}`;
}
