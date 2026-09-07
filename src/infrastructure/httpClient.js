const DEFAULT_TIMEOUT_MS = 7000;

export async function fetchWithTimeout(url, options = {}) {
  const timeoutMs = Number(options.timeoutMs ?? DEFAULT_TIMEOUT_MS);
  const retries = Number(options.retries ?? 0);
  let lastError = null;

  for (let attempt = 0; attempt <= retries; attempt += 1) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      });
      clearTimeout(timer);
      return response;
    } catch (error) {
      clearTimeout(timer);
      lastError = error;
      if (attempt === retries) {
        break;
      }
    }
  }

  if (lastError?.name === "AbortError") {
    throw new Error("Upstream request timed out.");
  }

  throw lastError || new Error("Upstream request failed.");
}

export async function mapWithConcurrency(items, concurrency, worker) {
  const size = Math.max(1, Number(concurrency) || 1);
  const results = new Array(items.length);
  let next = 0;

  async function run() {
    while (next < items.length) {
      const idx = next;
      next += 1;
      results[idx] = await worker(items[idx], idx);
    }
  }

  const runners = Array.from({ length: Math.min(size, items.length) }, () => run());
  await Promise.all(runners);
  return results;
}
