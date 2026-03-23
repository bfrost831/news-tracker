from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.article import Article
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()


class ArticleResponse(BaseModel):
    id: int
    title: str
    url: str
    source: str
    published_at: Optional[datetime]
    summary: Optional[str]
    image_url: Optional[str]

    class Config:
        from_attributes = True


@router.get("/story/{story_id}", response_model=list[ArticleResponse])
async def get_story_articles(
    story_id: int,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    from app.models.story import Story
    from sqlalchemy import Table, Column, Integer, Float, DateTime, MetaData, ForeignKey

    result = await db.execute(
        select(Article)
        .join(Article.__table__.alias(), False)  # placeholder - will use story_articles join table
        .order_by(desc(Article.published_at))
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()
