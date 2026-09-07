import { API_KEY_ROLES, AUTH_REQUIRED } from "../config/security.js";

function getRoleByKey(key) {
  if (!key) {
    return null;
  }
  const role = API_KEY_ROLES[key];
  return typeof role === "string" ? role : null;
}

export function attachUser(req, _res, next) {
  const apiKey = String(req.headers["x-api-key"] || "").trim();
  const role = getRoleByKey(apiKey);
  req.user = {
    apiKey: apiKey || null,
    role,
    isAuthenticated: Boolean(role)
  };
  next();
}

export function requireAuth(req, res, next) {
  if (!AUTH_REQUIRED) {
    return next();
  }

  if (!req.user?.isAuthenticated) {
    return res.status(401).json({
      ok: false,
      message: "Authentication required. Header x-api-key را ارسال کنید."
    });
  }

  return next();
}

export function requireRole(allowedRoles) {
  const allowed = new Set(allowedRoles);
  return (req, res, next) => {
    if (!AUTH_REQUIRED) {
      return next();
    }

    const role = req.user?.role;
    if (!role || !allowed.has(role)) {
      return res.status(403).json({
        ok: false,
        message: "Access denied for current role."
      });
    }

    return next();
  };
}
