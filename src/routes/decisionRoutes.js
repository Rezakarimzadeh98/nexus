import { Router } from "express";
import { validateDecisionQuery } from "../domain/validation.js";
import { fetchTimeseries } from "../infrastructure/frankfurterClient.js";
import { fetchOhlcForPairs } from "../infrastructure/ohlcClient.js";
import { getManualRecords } from "../infrastructure/manualRecordStore.js";
import { mergeRecords, summarize } from "../services/analyticsService.js";
import { fetchNewsAndAnalyze } from "../services/newsAnalysisService.js";
import { buildForecastBundle } from "../services/forecastService.js";
import { buildDecisionScore } from "../services/decisionService.js";

const decisionRouter = Router();

decisionRouter.get("/score", async (req, res) => {
  try {
    const query = validateDecisionQuery(req.query);

    const [onlineRows, manualRows, ohlcByTarget, news] = await Promise.all([
      fetchTimeseries(query),
      getManualRecords(),
      fetchOhlcForPairs(query),
      fetchNewsAndAnalyze({ query: query.newsQuery, max: query.newsMax })
    ]);

    const scopedManualRows = manualRows.filter(
      (row) => row.base === query.base && query.targets.includes(row.target)
    );

    const records = mergeRecords(onlineRows, scopedManualRows);
    const summary = summarize(records, ohlcByTarget);
    const forecast = buildForecastBundle(records, query.horizon);
    const score = buildDecisionScore({ summary, forecast, news });

    res.json({
      ok: true,
      query,
      source: "online+manual+news+ohlc",
      score,
      summary,
      forecast,
      news
    });
  } catch (error) {
    res.status(400).json({ ok: false, message: error.message });
  }
});

export default decisionRouter;
