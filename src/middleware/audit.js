import { appendAudit } from "../infrastructure/auditLogStore.js";

const sensitiveMethods = new Set(["POST", "PUT", "PATCH", "DELETE"]);

export function auditMiddleware(req, res, next) {
  const startedAt = Date.now();

  res.on("finish", () => {
    const shouldLog = sensitiveMethods.has(req.method) || req.path.startsWith("/api/decision") || req.path.startsWith("/api/forecast");
    if (!shouldLog) {
      return;
    }

    const event = {
      ts: new Date().toISOString(),
      method: req.method,
      path: req.originalUrl,
      status: res.statusCode,
      durationMs: Date.now() - startedAt,
      role: req.user?.role || null,
      authenticated: Boolean(req.user?.isAuthenticated),
      ip: req.ip || req.socket?.remoteAddress || null
    };

    appendAudit(event).catch(() => {
      // Ignore audit write errors to avoid impacting API responses.
    });
  });

  next();
}
