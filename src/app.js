import express from "express";
import path from "path";
import { fileURLToPath } from "url";
import fxRouter from "./routes/fxRoutes.js";
import manualRouter from "./routes/manualRoutes.js";
import analyticsRouter from "./routes/analyticsRoutes.js";
import newsRouter from "./routes/newsRoutes.js";
import forecastRouter from "./routes/forecastRoutes.js";
import decisionRouter from "./routes/decisionRoutes.js";
import adminRouter from "./routes/adminRoutes.js";
import marketRouter from "./routes/marketRoutes.js";
import { attachUser, requireAuth } from "./middleware/auth.js";
import { rateLimiter } from "./middleware/rateLimit.js";
import { auditMiddleware } from "./middleware/audit.js";

const app = express();
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const publicDir = path.join(__dirname, "..", "public");

app.use(express.json({ limit: "1mb" }));
app.use(attachUser);
app.use(rateLimiter);
app.use(auditMiddleware);

app.get("/api/health", (_req, res) => {
  res.json({ ok: true, service: "nexus-enterprise-fx", uptime: process.uptime() });
});

app.use("/api", requireAuth);

app.use("/api/fx", fxRouter);
app.use("/api/manual-records", manualRouter);
app.use("/api/analytics", analyticsRouter);
app.use("/api/news", newsRouter);
app.use("/api/forecast", forecastRouter);
app.use("/api/decision", decisionRouter);
app.use("/api/admin", adminRouter);
app.use("/api/market", marketRouter);

app.use(express.static(publicDir));

app.get("*", (_req, res) => {
  res.sendFile(path.join(publicDir, "index.html"));
});

export default app;
