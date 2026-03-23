"""Article-to-story semantic matcher using pgvector cosine similarity."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.models.story import Story
from app.models.article import Article

SIMILARITY_THRESHOLD = 0.75


async def match_articles_to_stories(db: AsyncSession, batch_size: int = 100) -> int:
    """Find unmatched articles and link them to stories above the similarity threshold."""
    # Get articles without embeddings that need processing
    result = await db.execute(
        select(Article)
        .where(Article.embedding.is_(None))
        .limit(batch_size)
    )
    articles = result.scalars().all()

    matched = 0
    for article in articles:
        if article.embedding is None:
            continue

        # Find stories with cosine similarity above threshold
        similar_stories = await db.execute(
            text("""
                SELECT id, 1 - (embedding <=> :embedding) AS similarity
                FROM stories
                WHERE embedding IS NOT NULL
                  AND is_public = true
                  AND 1 - (embedding <=> :embedding) > :threshold
                ORDER BY similarity DESC
                LIMIT 5
            """),
            {"embedding": article.embedding, "threshold": SIMILARITY_THRESHOLD}
        )

        for story_id, similarity in similar_stories:
            # Insert into story_articles (avoiding duplicates)
            await db.execute(
                text("""
                    INSERT INTO story_articles (story_id, article_id, relevance_score, matched_at)
                    VALUES (:story_id, :article_id, :score, NOW())
                    ON CONFLICT (story_id, article_id) DO NOTHING
                """),
                {"story_id": story_id, "article_id": article.id, "score": float(similarity)}
            )
            matched += 1

    await db.commit()
    return matched


async def embed_articles(articles: list[Article], db: AsyncSession) -> int:
    """Generate embeddings for articles using Gemini API."""
    # TODO: implement Gemini embedding API calls
    # import google.generativeai as genai
    # genai.configure(api_key=settings.gemini_api_key)
    return 0
