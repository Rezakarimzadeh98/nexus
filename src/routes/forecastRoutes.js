import { Router } from "express";
import { validateForecastQuery } from "../domain/validation.js";
import { fetchTimeseries } from "../infrastructure/frankfurterClient.js";
import { getManualRecords } from "../infrastructure/manualRecordStore.js";
import { mergeRecords } from "../services/analyticsService.js";
import { buildForecastBundle } from "../services/forecastService.js";

const forecastRouter = Router();

forecastRouter.get("/overview", async (req, res) => {
  try {
    const query = validateForecastQuery(req.query);
    const [onlineRowsResult, manualRowsResult] = await Promise.allSettled([
      fetchTimeseries(query),
      getManualRecords()
    ]);

    const onlineRows = onlineRowsResult.status === "fulfilled" ? onlineRowsResult.value : [];
    const manualRows = manualRowsResult.status === "fulfilled" ? manualRowsResult.value : [];

    if (!onlineRows.length && onlineRowsResult.status !== "fulfilled") {
      throw new Error("Live FX provider is temporarily unavailable.");
    }

    const scopedManualRows = manualRows.filter(
      (row) => row.base === query.base && query.targets.includes(row.target)
    );

    const records = mergeRecords(onlineRows, scopedManualRows);
    const forecast = buildForecastBundle(records, query.horizon);

    res.json({
      ok: true,
      query,
      source: "online+manual",
      forecast,
      warnings: manualRowsResult.status === "fulfilled" ? [] : ["Manual record store unavailable; using online data only."]
    });
  } catch (error) {
    res.status(400).json({ ok: false, message: error.message });
  }
});

export default forecastRouter;
