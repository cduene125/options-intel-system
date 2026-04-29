from dataclasses import dataclass
import requests

from config import settings


@dataclass
class NewsResult:
    sentiment: str
    score_adjustment: int
    risk_level: str
    headlines: list
    warnings: list
    summary: str


BULL = [
    "rally", "surge", "beats", "cooling inflation", "rate cut",
    "strong growth", "soft landing", "upgrade", "optimism"
]

BEAR = [
    "selloff", "plunge", "misses", "recession", "hot inflation",
    "rate hike", "hawkish", "downgrade", "war", "tariff", "weak demand"
]

HIGH = [
    "cpi", "inflation", "fomc", "fed", "powell", "jobs report",
    "pce", "gdp", "treasury yields", "rate decision"
]


def score_text(text: str):
    text_lower = text.lower()
    score = sum(word in text_lower for word in BULL) - sum(word in text_lower for word in BEAR)
    high_impact = any(word in text_lower for word in HIGH)
    return score, high_impact


def fetch_newsapi_headlines(limit=10):
    if not settings.news_api_key:
        return []

    try:
        url = "https://newsapi.org/v2/top-headlines"

        params = {
            "category": "business",
            "language": "en",
            "pageSize": limit,
            "apiKey": settings.news_api_key,
        }

        response = requests.get(url, params=params, timeout=12)
        response.raise_for_status()

        data = response.json()

        return [
            article.get("title", "")
            for article in data.get("articles", [])
            if article.get("title")
        ]

    except Exception as error:
        return [f"NewsAPI lookup failed: {error}"]


def analyze_news(limit=10):
    headlines = fetch_newsapi_headlines(limit)
    warnings = []

    if not headlines:
        return NewsResult(
            sentiment="NEUTRAL",
            score_adjustment=0,
            risk_level="UNKNOWN",
            headlines=[],
            warnings=["No NewsAPI key found. News sentiment inactive. Add NEWS_API_KEY to .env or Streamlit Secrets."],
            summary="News layer inactive. Using technicals and correlation only.",
        )

    if headlines[0].startswith("NewsAPI lookup failed"):
        return NewsResult(
            sentiment="NEUTRAL",
            score_adjustment=0,
            risk_level="ERROR",
            headlines=headlines,
            warnings=["NewsAPI lookup failed. Check your API key, activation email, or NewsAPI plan limits."],
            summary="News layer error. Using technicals and correlation only.",
        )

    score = 0
    high_impact_count = 0

    for headline in headlines:
        headline_score, high_impact = score_text(headline)
        score += headline_score
        high_impact_count += int(high_impact)

    sentiment = "BULLISH" if score >= 2 else "BEARISH" if score <= -2 else "NEUTRAL"

    adjustment = 5 if sentiment == "BULLISH" else -5 if sentiment == "BEARISH" else 0

    if high_impact_count >= 2:
        risk = "HIGH"
        warnings.append("Multiple high-impact macro/news keywords detected. Reduce size or wait.")
        adjustment -= 5
    elif high_impact_count == 1:
        risk = "MEDIUM"
        warnings.append("One high-impact macro/news keyword detected.")
    else:
        risk = "LOW"

    return NewsResult(
        sentiment=sentiment,
        score_adjustment=adjustment,
        risk_level=risk,
        headlines=headlines,
        warnings=warnings,
        summary=f"News sentiment: {sentiment}; risk level: {risk}; adjustment: {adjustment}.",
    )
