# Official data references used by NEXUS adapters

NEXUS ingests **public, documented feeds**. Each live source must list publisher, reference URL, and license note in `adapters/generic/sources.yaml`.

| Source id | Publisher | Reference |
| --- | --- | --- |
| `usgs-significant-month` | U.S. Geological Survey | https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php |
| `nasa-eonet-open` | NASA GSFC EONET | https://eonet.gsfc.nasa.gov/docs/v3 |
| `arxiv-cs-ai-lg` | arXiv (Cornell) | https://info.arxiv.org/help/api/index.html |
| `nvd-cves-recent` | NIST NVD | https://nvd.nist.gov/developers/vulnerabilities |
| `who-news-rss` | World Health Organization | https://www.who.int/ |

## Rules

1. Prefer official / intergovernmental / standards bodies over scraped HTML.  
2. Respect rate limits and terms linked above.  
3. Keep provenance on every observation (`source_id`, `raw_uri`, hashes).  
4. CI uses `sources.ci.yaml` fixtures so builds stay offline-reproducible; live ingest runs in workflows labeled `live` or locally.

## Disclaimer

Ingested content remains copyright of the respective publishers. NEXUS stores references and extracts for analysis; redistribution of full third-party content must follow each publisher’s terms.
