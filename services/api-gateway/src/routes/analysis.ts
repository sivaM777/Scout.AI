import type { FastifyInstance } from "fastify";
import { analyzeLinkRequestSchema, type AnalysisReport } from "@scout/shared";
import { buildAnalysisCacheKey } from "../services/analysis-key.js";
import type { CacheStore } from "../services/cache-store.js";
import type { AiClient } from "../services/ai-client.js";
import type { InMemoryAnalysisRepository } from "../repositories/memory-store.js";

type AnalysisRouteDeps = {
  cacheStore: CacheStore;
  aiClient: AiClient;
  analysisRepository: InMemoryAnalysisRepository;
  cacheTtlSeconds: number;
};

export async function registerAnalysisRoutes(app: FastifyInstance, deps: AnalysisRouteDeps): Promise<void> {
  app.post("/v1/analysis", async (request, reply) => {
    const payload = analyzeLinkRequestSchema.parse(request.body);
    const cacheKey = buildAnalysisCacheKey(payload.url);
    const cachedReport = await deps.cacheStore.get<AnalysisReport>(cacheKey);

    if (cachedReport) {
      deps.analysisRepository.save(cachedReport);
      return {
        source: "cache",
        report: cachedReport,
      };
    }

    const freshReport = await deps.aiClient.analyze(payload);
    deps.analysisRepository.save(freshReport);
    await deps.cacheStore.set(cacheKey, freshReport, deps.cacheTtlSeconds);

    return reply.code(200).send({
      source: "fresh",
      report: freshReport,
    });
  });

  app.get("/v1/analysis/recent", async () => ({
    items: deps.analysisRepository.listRecent(),
  }));

  app.get<{ Params: { analysisId: string } }>("/v1/analysis/:analysisId", async (request, reply) => {
    const report = deps.analysisRepository.get(request.params.analysisId);

    if (!report) {
      return reply.code(404).send({
        message: "Analysis not found.",
      });
    }

    return report;
  });
}
