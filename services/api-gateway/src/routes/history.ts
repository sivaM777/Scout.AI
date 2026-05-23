import type { FastifyInstance } from "fastify";
import type { InMemoryAnalysisRepository } from "../repositories/memory-store.js";

export async function registerHistoryRoutes(
  app: FastifyInstance,
  analysisRepository: InMemoryAnalysisRepository,
): Promise<void> {
  app.get("/v1/history", async () => ({
    items: analysisRepository.listRecent(50),
  }));
}
