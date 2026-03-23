from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.models.story import Story
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class StoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    seed_keywords: list[str] = []


class StoryResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str]
    follower_count: int
    article_count: int
    is_public: bool

    class Config:
        from_attributes = True


@router.get("/", response_model=list[StoryResponse])
async def list_stories(
    limit: int = Query(20, le=100),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Story)
        .where(Story.is_public == True)
        .order_by(desc(Story.article_count))
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()


@router.get("/trending", response_model=list[StoryResponse])
async def trending_stories(
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Story)
        .where(Story.is_public == True)
        .order_by(desc(Story.last_article_at))
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/{slug}", response_model=StoryResponse)
async def get_story(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Story).where(Story.slug == slug))
    story = result.scalar_one_or_none()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return story


@router.post("/", response_model=StoryResponse, status_code=201)
async def create_story(data: StoryCreate, db: AsyncSession = Depends(get_db)):
    slug = data.name.lower().replace(" ", "-").replace("/", "-")[:100]
    story = Story(
        name=data.name,
        slug=slug,
        description=data.description,
        seed_keywords=data.seed_keywords,
        is_public=False,  # user-created stories are private by default
    )
    db.add(story)
    await db.commit()
    await db.refresh(story)
    return story
