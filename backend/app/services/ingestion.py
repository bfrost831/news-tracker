"""Article ingestion pipeline - pulls from news-aggregator and SearXNG."""
import hashlib
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.models.article import Article
import feedparser
from datetime import datetime


async def fetch_from_aggregator(client: httpx.AsyncClient) -> list[dict]:
    """Fetch articles from local news-aggregator service."""
    try:
        resp = await client.get(f"{settings.news_aggregator_url}/articles", timeout=10)
        return resp.json().get("articles", [])
    except Exception as e:
        print(f"Error fetching from aggregator: {e}")
        return []


async def fetch_rss(url: str, client: httpx.AsyncClient) -> list[dict]:
    """Fetch and parse an RSS feed."""
    try:
        resp = await client.get(url, timeout=10)
        feed = feedparser.parse(resp.text)
        articles = []
        for entry in feed.entries[:20]:
            articles.append({
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "source": feed.feed.get("title", url),
                "published_at": entry.get("published", None),
                "summary": entry.get("summary", ""),
            })
        return articles
    except Exception as e:
        print(f"Error fetching RSS {url}: {e}")
        return []


def compute_content_hash(title: str, url: str) -> str:
    return hashlib.sha256(f"{url}:{title}".encode()).hexdigest()[:64]


async def ingest_articles(raw_articles: list[dict], db: AsyncSession) -> int:
    """Ingest a list of raw article dicts, deduplicating by URL and content hash."""
    ingested = 0
    for raw in raw_articles:
        url = raw.get("url", "")
        if not url:
            continue

        content_hash = compute_content_hash(raw.get("title", ""), url)

        # Check for duplicates
        existing = await db.execute(
            select(Article).where(Article.url == url)
        )
        if existing.scalar_one_or_none():
            continue

        article = Article(
            title=raw.get("title", "")[:500],
            url=url[:1000],
            source=raw.get("source", "unknown")[:100],
            summary=raw.get("summary", ""),
            content_hash=content_hash,
            image_url=raw.get("image_url"),
        )
        db.add(article)
        ingested += 1

    await db.commit()
    return ingested
