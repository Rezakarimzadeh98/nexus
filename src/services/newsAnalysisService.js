const POSITIVE_WORDS = [
  "gain",
  "gains",
  "rise",
  "rises",
  "rally",
  "up",
  "beat",
  "strong",
  "growth",
  "surge",
  "optimism",
  "record",
  "bull",
  "rebound"
];

const NEGATIVE_WORDS = [
  "drop",
  "drops",
  "fall",
  "falls",
  "down",
  "slump",
  "weak",
  "decline",
  "risk",
  "crash",
  "fear",
  "loss",
  "bear",
  "recession"
];

export async function fetchNewsAndAnalyze({ query, max = 20 }) {
  const url = `https://news.google.com/rss/search?q=${encodeURIComponent(query)}&hl=en-US&gl=US&ceid=US:en`;
  const response = await fetch(url, { headers: { Accept: "application/xml,text/xml" } });
  if (!response.ok) {
    throw new Error(`News provider error: ${response.status}`);
  }

  const xml = await response.text();
  const items = parseRssItems(xml).slice(0, max);

  const sentimentSummary = {
    positive: 0,
    negative: 0,
    neutral: 0,
    score: 0
  };

  const enriched = items.map((item) => {
    const sentiment = classifySentiment(item.title);
    sentimentSummary[sentiment.label] += 1;
    sentimentSummary.score += sentiment.score;

    return {
      ...item,
      sentiment: sentiment.label,
      sentimentScore: sentiment.score
    };
  });

  const avgScore = enriched.length ? sentimentSummary.score / enriched.length : 0;
  return {
    query,
    source: "google-news-rss",
    totalArticles: enriched.length,
    sentiment: {
      positive: sentimentSummary.positive,
      negative: sentimentSummary.negative,
      neutral: sentimentSummary.neutral,
      averageScore: Number(avgScore.toFixed(3))
    },
    articles: enriched
  };
}

function parseRssItems(xml) {
  const itemBlocks = xml.match(/<item>[\s\S]*?<\/item>/g) || [];
  return itemBlocks.map((block) => {
    const title = decodeXml(extractTag(block, "title"));
    const link = decodeXml(extractTag(block, "link"));
    const pubDate = decodeXml(extractTag(block, "pubDate"));
    const source = decodeXml(extractTag(block, "source"));
    return { title, link, pubDate, source };
  });
}

function extractTag(block, tag) {
  const match = block.match(new RegExp(`<${tag}[^>]*>([\\s\\S]*?)<\\/${tag}>`, "i"));
  return match ? match[1].trim() : "";
}

function decodeXml(text) {
  return String(text || "")
    .replace(/<!\[CDATA\[|\]\]>/g, "")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'");
}

function classifySentiment(title) {
  const lowered = String(title || "").toLowerCase();
  let score = 0;

  for (const word of POSITIVE_WORDS) {
    if (lowered.includes(word)) {
      score += 1;
    }
  }

  for (const word of NEGATIVE_WORDS) {
    if (lowered.includes(word)) {
      score -= 1;
    }
  }

  if (score > 0) {
    return { label: "positive", score };
  }
  if (score < 0) {
    return { label: "negative", score };
  }
  return { label: "neutral", score: 0 };
}
