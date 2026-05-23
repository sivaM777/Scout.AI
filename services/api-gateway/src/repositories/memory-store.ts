import type { AnalysisReport, WatchlistItem } from "@scout/shared";

export class InMemoryAnalysisRepository {
  private readonly reports = new Map<string, AnalysisReport>();

  save(report: AnalysisReport): void {
    this.reports.set(report.id, report);
  }

  get(reportId: string): AnalysisReport | null {
    return this.reports.get(reportId) ?? null;
  }

  listRecent(limit = 20): AnalysisReport[] {
    return [...this.reports.values()]
      .sort((left, right) => right.generatedAt.localeCompare(left.generatedAt))
      .slice(0, limit);
  }
}

export class InMemoryWatchlistRepository {
  private readonly items = new Map<string, WatchlistItem>();

  add(item: WatchlistItem): WatchlistItem {
    this.items.set(item.id, item);
    return item;
  }

  list(): WatchlistItem[] {
    return [...this.items.values()].sort((left, right) => right.addedAt.localeCompare(left.addedAt));
  }
}
