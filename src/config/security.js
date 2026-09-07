export const AUTH_REQUIRED = process.env.AUTH_REQUIRED !== "false";

const defaultApiKeyRoles = {
  "nexus-admin-2026": "admin",
  "nexus-analyst-2026": "analyst",
  "nexus-viewer-2026": "viewer"
};

function parseApiKeysFromEnv() {
  const raw = process.env.API_KEY_ROLES_JSON;
  if (!raw) {
    return null;
  }
  try {
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

export const API_KEY_ROLES = parseApiKeysFromEnv() || defaultApiKeyRoles;

export const RATE_LIMIT_WINDOW_MS = 60 * 1000;
export const RATE_LIMIT_MAX = 120;

export const AUDIT_LOG_PATH = "./data/audit.log";
