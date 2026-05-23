import "dotenv/config";
import { z } from "zod";

const configSchema = z.object({
  PORT: z.coerce.number().default(4000),
  HOST: z.string().default("0.0.0.0"),
  AI_SERVICE_URL: z.string().url().default("http://localhost:8000"),
  REDIS_URL: z.string().optional(),
  CORS_ORIGIN: z.string().default("*"),
  CACHE_TTL_SECONDS: z.coerce.number().default(60 * 60 * 6),
});

export type AppConfig = {
  port: number;
  host: string;
  aiServiceUrl: string;
  redisUrl?: string;
  corsOrigin: string;
  cacheTtlSeconds: number;
};

export const config: AppConfig = (() => {
  const parsed = configSchema.parse(process.env);

  return {
    port: parsed.PORT,
    host: parsed.HOST,
    aiServiceUrl: parsed.AI_SERVICE_URL,
    redisUrl: parsed.REDIS_URL,
    corsOrigin: parsed.CORS_ORIGIN,
    cacheTtlSeconds: parsed.CACHE_TTL_SECONDS,
  };
})();
