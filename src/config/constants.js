export const APP_PORT = process.env.PORT ? Number(process.env.PORT) : 8080;

export const DATA_FILE_PATH = "./data/manual-records.json";

export const FX_API_BASE = "https://api.frankfurter.app";

export const ISO_CURRENCY = /^[A-Z]{3}$/;

export const MAX_DAYS = 365;

export const MAX_TARGETS = 10;

export const MAX_FORECAST_HORIZON = 30;

export const MIN_FORECAST_POINTS = 20;
