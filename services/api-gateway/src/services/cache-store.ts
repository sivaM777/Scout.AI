import Redis from "ioredis";

type MemoryEntry = {
  payload: string;
  expiresAt: number;
};

export interface CacheStore {
  get<T>(key: string): Promise<T | null>;
  set<T>(key: string, value: T, ttlSeconds: number): Promise<void>;
  close(): Promise<void>;
  mode: "memory" | "redis";
}

class MemoryCacheStore implements CacheStore {
  private readonly store = new Map<string, MemoryEntry>();

  public readonly mode = "memory" as const;

  async get<T>(key: string): Promise<T | null> {
    const entry = this.store.get(key);
    if (!entry) {
      return null;
    }

    if (entry.expiresAt <= Date.now()) {
      this.store.delete(key);
      return null;
    }

    return JSON.parse(entry.payload) as T;
  }

  async set<T>(key: string, value: T, ttlSeconds: number): Promise<void> {
    this.store.set(key, {
      payload: JSON.stringify(value),
      expiresAt: Date.now() + ttlSeconds * 1000,
    });
  }

  async close(): Promise<void> {
    this.store.clear();
  }
}

class RedisCacheStore implements CacheStore {
  public readonly mode = "redis" as const;

  constructor(private readonly client: Redis) {}

  async get<T>(key: string): Promise<T | null> {
    const payload = await this.client.get(key);
    return payload ? (JSON.parse(payload) as T) : null;
  }

  async set<T>(key: string, value: T, ttlSeconds: number): Promise<void> {
    await this.client.set(key, JSON.stringify(value), "EX", ttlSeconds);
  }

  async close(): Promise<void> {
    await this.client.quit();
  }
}

export async function createCacheStore(redisUrl?: string): Promise<CacheStore> {
  if (!redisUrl) {
    return new MemoryCacheStore();
  }

  try {
    const client = new Redis(redisUrl, {
      maxRetriesPerRequest: 1,
      enableOfflineQueue: false,
    });

    await client.ping();
    return new RedisCacheStore(client);
  } catch {
    return new MemoryCacheStore();
  }
}
