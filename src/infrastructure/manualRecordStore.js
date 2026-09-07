import { promises as fs } from "fs";
import { DATA_FILE_PATH } from "../config/constants.js";

async function ensureDataFile() {
  try {
    await fs.access(DATA_FILE_PATH);
  } catch {
    await fs.writeFile(DATA_FILE_PATH, "[]", "utf-8");
  }
}

export async function getManualRecords() {
  await ensureDataFile();
  const raw = await fs.readFile(DATA_FILE_PATH, "utf-8");
  const parsed = JSON.parse(raw);
  return Array.isArray(parsed) ? parsed : [];
}

export async function saveManualRecords(records) {
  await ensureDataFile();
  await fs.writeFile(DATA_FILE_PATH, JSON.stringify(records, null, 2), "utf-8");
}

export async function upsertManualRecord(record) {
  const rows = await getManualRecords();
  const key = `${record.date}|${record.base}|${record.target}`;
  const map = new Map(rows.map((r) => [`${r.date}|${r.base}|${r.target}`, r]));
  map.set(key, record);
  const nextRows = Array.from(map.values()).sort((a, b) => (a.date > b.date ? 1 : -1));
  await saveManualRecords(nextRows);
  return nextRows;
}
