import { RATE_LIMIT_MAX, RATE_LIMIT_WINDOW_MS } from "../config/security.js";

const buckets = new Map();

function keyFor(req) {
  const ip = req.ip || req.socket?.remoteAddress || "unknown";
  const apiKey = req.user?.apiKey || "no-key";
  return `${ip}:${apiKey}`;
}

export function rateLimiter(req, res, next) {
  const now = Date.now();
  const key = keyFor(req);
  const item = buckets.get(key) || { count: 0, resetAt: now + RATE_LIMIT_WINDOW_MS };

  if (now > item.resetAt) {
    item.count = 0;
    item.resetAt = now + RATE_LIMIT_WINDOW_MS;
  }

  item.count += 1;
  buckets.set(key, item);

  const remaining = Math.max(RATE_LIMIT_MAX - item.count, 0);
  res.setHeader("x-ratelimit-limit", String(RATE_LIMIT_MAX));
  res.setHeader("x-ratelimit-remaining", String(remaining));
  res.setHeader("x-ratelimit-reset", String(Math.ceil(item.resetAt / 1000)));

  if (item.count > RATE_LIMIT_MAX) {
    return res.status(429).json({
      ok: false,
      message: "Too many requests. Try again later."
    });
  }

  return next();
}
