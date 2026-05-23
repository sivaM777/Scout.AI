import type { FastifyInstance } from "fastify";

export async function registerHealthRoutes(app: FastifyInstance, mode: "memory" | "redis"): Promise<void> {
  app.get("/health", async () => ({
    status: "ok",
    cache: mode,
    timestamp: new Date().toISOString(),
  }));
}
