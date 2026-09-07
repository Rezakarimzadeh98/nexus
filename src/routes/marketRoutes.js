import { Router } from "express";
import { validateMarketQuery, validateAnalysisMode } from "../domain/validation.js";
import { resolveSymbols, fetchMarketSeries } from "../infrastructure/marketDataClient.js";
import { summarize } from "../services/analyticsService.js";
import { buildForecastBundle } from "../services/forecastService.js";
import { fetchNewsAndAnalyze } from "../services/newsAnalysisService.js";
import { buildDecisionScore } from "../services/decisionService.js";

const marketRouter = Router();

function buildPredictionMethod() {
  return {
    model: "Holt linear trend",
    details: [
      "Series model: level+trend exponential smoothing with alpha=0.35 and beta=0.20.",
      "Forecast horizon: iterative point forecast for m=1..h using level + m*trend.",
      "Uncertainty band: 95% interval via residual sigma scaled by sqrt(step).",
      "Quality metrics: MAE, RMSE, MAPE from rolling one-step backtest.",
      "Decision score: weighted blend of technical score, forecast score, and news sentiment score."
    ]
  };
}

marketRouter.get("/overview", async (req, res) => {
  try {
    const query = validateMarketQuery(req.query);
    const symbols = resolveSymbols(query);
    const data = await fetchMarketSeries({ ...query, symbols });

    if (!data.records.length) {
      throw new Error("No market records available from provider for requested symbols.");
    }

    const summary = summarize(data.records, data.ohlcByTarget);
    res.json({
      ok: true,
      source: "market-online",
      query: { ...query, symbols },
      summary,
      records: data.records,
      warnings: []
    });
  } catch (error) {
    res.status(400).json({ ok: false, message: error.message });
  }
});

marketRouter.get("/forecast", async (req, res) => {
  try {
    const query = validateMarketQuery(req.query);
    const horizon = Number(req.query.horizon || 7);
    if (!Number.isInteger(horizon) || horizon < 1 || horizon > 30) {
      throw new Error("horizon باید بین 1 تا 30 باشد.");
    }

    const symbols = resolveSymbols(query);
    const data = await fetchMarketSeries({ ...query, symbols });
    if (!data.records.length) {
      throw new Error("No market records available from provider for requested symbols.");
    }

    const forecast = buildForecastBundle(data.records, horizon);
    res.json({
      ok: true,
      source: "market-online",
      query: { ...query, symbols, horizon },
      forecast,
      predictionMethod: buildPredictionMethod()
    });
  } catch (error) {
    res.status(400).json({ ok: false, message: error.message });
  }
});

marketRouter.get("/decision", async (req, res) => {
  try {
    const query = validateMarketQuery(req.query);
    const horizon = Number(req.query.horizon || 7);
    const newsQuery = String(req.query.newsQuery || `${query.market} market`).trim();
    const newsMax = Number(req.query.newsMax || 20);
    const analysisMode = validateAnalysisMode(req.query.analysisMode || "hybrid");

    if (!Number.isInteger(horizon) || horizon < 1 || horizon > 30) {
      throw new Error("horizon باید بین 1 تا 30 باشد.");
    }
    if (!Number.isInteger(newsMax) || newsMax < 1 || newsMax > 50) {
      throw new Error("newsMax باید بین 1 تا 50 باشد.");
    }

    const symbols = resolveSymbols(query);
    const [marketResult, newsResult] = await Promise.allSettled([
      fetchMarketSeries({ ...query, symbols }),
      fetchNewsAndAnalyze({ query: newsQuery, max: newsMax })
    ]);

    const marketData = marketResult.status === "fulfilled" ? marketResult.value : { records: [], ohlcByTarget: new Map() };
    if (!marketData.records.length) {
      throw new Error("No market records available from provider for requested symbols.");
    }

    const news =
      newsResult.status === "fulfilled"
        ? newsResult.value
        : {
            query: newsQuery,
            source: "google-news-rss",
            totalArticles: 0,
            sentiment: { positive: 0, negative: 0, neutral: 0, averageScore: 0 },
            articles: []
          };

    const summary = summarize(marketData.records, marketData.ohlcByTarget);
    const forecast = buildForecastBundle(marketData.records, horizon);
    const score = buildDecisionScore({ summary, forecast, news, mode: analysisMode });

    res.json({
      ok: true,
      source: "market-online+news",
      query: { ...query, symbols, horizon, newsQuery, newsMax, analysisMode },
      score,
      summary,
      forecast,
      news,
      predictionMethod: buildPredictionMethod(),
      warnings: newsResult.status === "fulfilled" ? [] : ["News provider unavailable; sentiment fallback applied."]
    });
  } catch (error) {
    res.status(400).json({ ok: false, message: error.message });
  }
});

export default marketRouter;
