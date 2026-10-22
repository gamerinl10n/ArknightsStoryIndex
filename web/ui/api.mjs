import { t } from "./dom.mjs";

/** Per-tab, bounded LRU. No disk storage, cached failures, or shared aborted requests. */
export function createClient({
  limit = 16,
  ttl = 60000,
  now = () => Date.now(),
} = {}) {
  const cache = new Map(),
    pending = new Map();
  async function request(url, { signal } = {}) {
    if (signal?.aborted) throw new DOMException("Aborted", "AbortError");
    const hit = cache.get(url);
    if (hit && hit.expires > now()) {
      cache.delete(url);
      cache.set(url, hit);
      return hit.data;
    }
    cache.delete(url);
    if (!signal && pending.has(url)) return pending.get(url);
    const task = (async () => {
      const response = await fetch(url, signal ? { signal } : undefined);
      if (!response.ok) throw Error(t("failed"));
      const data = await response.json();
      if (signal?.aborted) throw new DOMException("Aborted", "AbortError");
      cache.set(url, { data, expires: now() + ttl });
      while (cache.size > limit) cache.delete(cache.keys().next().value);
      return data;
    })();
    if (!signal) pending.set(url, task);
    try {
      return await task;
    } finally {
      if (pending.get(url) === task) pending.delete(url);
    }
  }
  return request;
}
export const api = createClient();
