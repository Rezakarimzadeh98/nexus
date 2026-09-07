import { Router } from "express";
import { validateTimeseriesQuery } from "../domain/validation.js";
import { fetchTimeseries } from "../infrastructure/frankfurterClient.js";
import { fetchOhlcForPairs } from "../infrastructure/ohlcClient.js";
import { getManualRecords } from "../infrastructure/manualRecordStore.js";
import { mergeRecords, summarize } from "../services/analyticsService.js";

const analyticsRouter = Router();

analyticsRouter.get("/overview", async (req, res) => {
  try {
    const query = validateTimeseriesQuery(req.query);
    const [onlineRowsResult, manualRowsResult, ohlcByTargetResult] = await Promise.allSettled([
      fetchTimeseries(query),
      getManualRecords(),
      fetchOhlcForPairs(query)
    ]);

    const onlineRows = onlineRowsResult.status === "fulfilled" ? onlineRowsResult.value : [];
    const manualRows = manualRowsResult.status === "fulfilled" ? manualRowsResult.value : [];
    const ohlcByTarget = ohlcByTargetResult.status === "fulfilled" ? ohlcByTargetResult.value : new Map();

    if (!onlineRows.length && onlineRowsResult.status !== "fulfilled") {
      throw new Error("Live FX provider is temporarily unavailable.");
    }

    const scopedManualRows = manualRows.filter(
      (row) => row.base === query.base && query.targets.includes(row.target)
    );

    const records = mergeRecords(onlineRows, scopedManualRows);
    const summary = summarize(records, ohlcByTarget);
    const warnings = [];
    if (ohlcByTargetResult.status !== "fulfilled") {
      warnings.push("OHLC provider unavailable; technical OHLC enrichments were skipped.");
    }
    res.json({ ok: true, source: "online+manual", query, summary, records, warnings });
  } catch (error) {
    res.status(400).json({ ok: false, message: error.message });
  }
});

export default analyticsRouter;
