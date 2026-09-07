import { promises as fs } from "fs";
import { AUDIT_LOG_PATH } from "../config/security.js";

async function ensureLogFile() {
  try {
    await fs.access(AUDIT_LOG_PATH);
  } catch {
    await fs.writeFile(AUDIT_LOG_PATH, "", "utf-8");
  }
}

export async function appendAudit(event) {
  await ensureLogFile();
  const line = JSON.stringify(event) + "\n";
  await fs.appendFile(AUDIT_LOG_PATH, line, "utf-8");
}

export async function readAudit(limit = 200) {
  await ensureLogFile();
  const text = await fs.readFile(AUDIT_LOG_PATH, "utf-8");
  const lines = text.trim() ? text.trim().split(/\r?\n/) : [];
  const events = lines
    .slice(-Math.max(1, Math.min(limit, 1000)))
    .map((line) => {
      try {
        return JSON.parse(line);
      } catch {
        return null;
      }
    })
    .filter(Boolean);
  return events.reverse();
}
