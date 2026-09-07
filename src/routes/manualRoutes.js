import { Router } from "express";
import { validateManualRecord } from "../domain/validation.js";
import { getManualRecords, upsertManualRecord } from "../infrastructure/manualRecordStore.js";
import { requireRole } from "../middleware/auth.js";

const manualRouter = Router();

manualRouter.get("/", async (_req, res) => {
  const rows = await getManualRecords();
  res.json({ ok: true, records: rows });
});

manualRouter.post("/", requireRole(["admin", "analyst"]), async (req, res) => {
  try {
    const normalized = validateManualRecord(req.body || {});
    const rows = await upsertManualRecord(normalized);
    res.status(201).json({ ok: true, records: rows });
  } catch (error) {
    res.status(400).json({ ok: false, message: error.message });
  }
});

export default manualRouter;
