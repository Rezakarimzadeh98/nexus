import { Router } from "express";
import { validateTimeseriesQuery } from "../domain/validation.js";
import { fetchTimeseries } from "../infrastructure/frankfurterClient.js";

const fxRouter = Router();

fxRouter.get("/timeseries", async (req, res) => {
  try {
    const query = validateTimeseriesQuery(req.query);
    const rows = await fetchTimeseries(query);
    res.json({
      ok: true,
      source: "frankfurter_ecb",
      query,
      records: rows
    });
  } catch (error) {
    res.status(400).json({ ok: false, message: error.message });
  }
});

export default fxRouter;
