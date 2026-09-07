import { Router } from "express";
import { fetchNewsAndAnalyze } from "../services/newsAnalysisService.js";

const newsRouter = Router();

newsRouter.get("/analyze", async (req, res) => {
  try {
    const query = String(req.query.query || "forex").trim();
    const max = Number(req.query.max || 20);
    if (!query) {
      throw new Error("query الزامی است.");
    }
    if (!Number.isInteger(max) || max < 1 || max > 50) {
      throw new Error("max باید بین 1 تا 50 باشد.");
    }

    const result = await fetchNewsAndAnalyze({ query, max });
    res.json({ ok: true, ...result });
  } catch (error) {
    res.status(400).json({ ok: false, message: error.message });
  }
});

export default newsRouter;
