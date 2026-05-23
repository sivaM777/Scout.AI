import Fastify from "fastify";
import cors from "@fastify/cors";
import sensible from "@fastify/sensible";
import { config } from "./config.js";
import { createAiClient } from "./services/ai-client.js";
import { createCacheStore } from "./services/cache-store.js";
import { InMemoryAnalysisRepository, InMemoryWatchlistRepository } from "./repositories/memory-store.js";
import { registerHealthRoutes } from "./routes/health.js";
import { registerAnalysisRoutes } from "./routes/analysis.js";
import { registerHistoryRoutes } from "./routes/history.js";
import { registerWatchlistRoutes } from "./routes/watchlist.js";

export async function buildApp() {
  const app = Fastify({
    logger: true,
  });

  await app.register(cors, {
    origin: config.corsOrigin,
  });

  await app.register(sensible);

  const cacheStore = await createCacheStore(config.redisUrl);
  const analysisRepository = new InMemoryAnalysisRepository();
  const watchlistRepository = new InMemoryWatchlistRepository();
  const aiClient = createAiClient(config.aiServiceUrl);

  await registerHealthRoutes(app, cacheStore.mode);
  await registerAnalysisRoutes(app, {
    cacheStore,
    aiClient,
    analysisRepository,
    cacheTtlSeconds: config.cacheTtlSeconds,
  });
  await registerHistoryRoutes(app, analysisRepository);
  await registerWatchlistRoutes(app, watchlistRepository);

  app.addHook("onClose", async () => {
    await cacheStore.close();
  });

  return app;
}
