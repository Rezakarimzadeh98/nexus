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
    const [onlineRows, manualRows, ohlcByTarget] = await Promise.all([
      fetchTimeseries(query),
      getManualRecords(),
      fetchOhlcForPairs(query)
    ]);

    const scopedManualRows = manualRows.filter(
      (row) => row.base === query.base && query.targets.includes(row.target)
    );

    const records = mergeRecords(onlineRows, scopedManualRows);
    const summary = summarize(records, ohlcByTarget);
    res.json({ ok: true, source: "online+manual", query, summary, records });
  } catch (error) {
    res.status(400).json({ ok: false, message: error.message });
  }
});

export default analyticsRouter;
