from sqlalchemy import String, Integer, DateTime, Boolean, ARRAY, func
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from datetime import datetime
from app.core.database import Base


class Story(Base):
    __tablename__ = "stories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000))
    seed_keywords: Mapped[list[str]] = mapped_column(ARRAY(String), default=[])
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768))
    created_by: Mapped[int | None] = mapped_column(Integer)  # user_id, null = system
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    follower_count: Mapped[int] = mapped_column(Integer, default=0)
    article_count: Mapped[int] = mapped_column(Integer, default=0)
    last_article_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
