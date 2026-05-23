import { randomUUID } from "node:crypto";
import type { FastifyInstance } from "fastify";
import { z } from "zod";
import { watchlistItemSchema } from "@scout/shared";
import type { InMemoryWatchlistRepository } from "../repositories/memory-store.js";

const createWatchlistInputSchema = watchlistItemSchema
  .omit({
    id: true,
    addedAt: true,
  })
  .extend({
    note: z.string().max(160).optional(),
    targetPrice: z.number().positive().optional(),
  });

export async function registerWatchlistRoutes(
  app: FastifyInstance,
  watchlistRepository: InMemoryWatchlistRepository,
): Promise<void> {
  app.get("/v1/watchlist", async () => ({
    items: watchlistRepository.list(),
  }));

  app.post("/v1/watchlist", async (request, reply) => {
    const payload = createWatchlistInputSchema.parse(request.body);
    const item = watchlistItemSchema.parse({
      ...payload,
      id: randomUUID(),
      addedAt: new Date().toISOString(),
    });

    return reply.code(201).send({
      item: watchlistRepository.add(item),
    });
  });
}
