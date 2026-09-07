import { Router } from "express";
import { readAudit } from "../infrastructure/auditLogStore.js";
import { requireRole } from "../middleware/auth.js";

const adminRouter = Router();

adminRouter.get("/audit", requireRole(["admin"]), async (req, res) => {
  const limit = Number(req.query.limit || 200);
  const boundedLimit = Number.isInteger(limit) ? Math.max(1, Math.min(limit, 1000)) : 200;
  const events = await readAudit(boundedLimit);
  res.json({ ok: true, limit: boundedLimit, events });
});

adminRouter.get("/me", (req, res) => {
  res.json({
    ok: true,
    user: {
      role: req.user?.role || null,
      authenticated: Boolean(req.user?.isAuthenticated)
    }
  });
});

export default adminRouter;
