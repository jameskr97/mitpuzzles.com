import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import DateTime, Boolean, Text, ForeignKey, select, desc, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import selectinload

from app.dependencies import AsyncDatabase
from app.models import Base
from app.modules.authentication import User, fastapi_users


# Models

class NewsPost(Base):
    __tablename__ = "news_post"

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, server_default=text("uuidv7()"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False), nullable=True)

    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False)

    author: Mapped["User"] = relationship("User", lazy="raise")


# Schemas

class NewsPostCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=50000)
    is_published: bool = False


class NewsPostUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=50000)
    is_published: Optional[bool] = None


class NewsPostResponse(BaseModel):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    content: str
    is_published: bool
    published_at: Optional[datetime]
    author_username: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class NewsFeedResponse(BaseModel):
    posts: list[NewsPostResponse]
    has_more: bool
    total: int


# Service

class NewsService:
    def __init__(self, db: AsyncDatabase):
        self.db = db

    async def create_post(self, data: NewsPostCreate, author_id: uuid.UUID) -> NewsPost:
        post = NewsPost(
            content=data.content,
            is_published=data.is_published,
            published_at=datetime.utcnow() if data.is_published else None,
            author_id=author_id,
        )
        self.db.add(post)
        await self.db.commit()
        await self.db.refresh(post)
        return post

    async def update_post(self, post_id: uuid.UUID, data: NewsPostUpdate) -> NewsPost:
        result = await self.db.execute(select(NewsPost).where(NewsPost.id == post_id))
        post = result.scalar_one_or_none()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        if data.content is not None:
            post.content = data.content
        if data.is_published is not None:
            was_published = post.is_published
            post.is_published = data.is_published
            if data.is_published and not was_published:
                post.published_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(post)
        return post

    async def delete_post(self, post_id: uuid.UUID) -> None:
        result = await self.db.execute(select(NewsPost).where(NewsPost.id == post_id))
        post = result.scalar_one_or_none()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        await self.db.delete(post)
        await self.db.commit()

    def _to_response(self, post: NewsPost) -> NewsPostResponse:
        return NewsPostResponse(
            id=post.id,
            created_at=post.created_at,
            updated_at=post.updated_at,
            content=post.content,
            is_published=post.is_published,
            published_at=post.published_at,
            author_username=post.author.username if post.author else None,
        )

    async def list_all(self) -> list[NewsPostResponse]:
        """All posts including drafts (admin view)."""
        result = await self.db.execute(select(NewsPost).options(selectinload(NewsPost.author)).order_by(desc(NewsPost.created_at)))
        return [self._to_response(p) for p in result.scalars().all()]

    async def get_feed(self, limit: int = 20, offset: int = 0) -> NewsFeedResponse:
        """Published posts, newest first."""
        base = select(NewsPost).where(NewsPost.is_published == True)

        count_result = await self.db.execute(select(func.count()).select_from(base.subquery()))
        total = count_result.scalar()

        query = base.options(selectinload(NewsPost.author)).order_by(desc(NewsPost.published_at)).limit(limit).offset(offset)
        result = await self.db.execute(query)
        posts = [self._to_response(p) for p in result.scalars().all()]

        return NewsFeedResponse(
            posts=posts,
            has_more=(offset + limit) < total,
            total=total,
        )


# Routes

router = APIRouter(prefix="/api/news", tags=["News"])


@router.get("/feed", response_model=NewsFeedResponse)
async def get_news_feed(
    db: AsyncDatabase,
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
):
    """Public news feed — published updates, newest first."""
    service = NewsService(db)
    return await service.get_feed(limit=limit, offset=offset)


# Admin routes

@router.get("/admin/list", response_model=list[NewsPostResponse])
async def list_all_posts(
    db: AsyncDatabase,
    user: User = Depends(fastapi_users.current_user(active=True, superuser=True)),
):
    """List all posts including drafts. Admin only."""
    service = NewsService(db)
    return await service.list_all()


@router.post("/admin", response_model=NewsPostResponse, status_code=201)
async def create_post(
    data: NewsPostCreate,
    db: AsyncDatabase,
    user: User = Depends(fastapi_users.current_user(active=True, superuser=True)),
):
    """Create a news post. Admin only."""
    service = NewsService(db)
    post = await service.create_post(data=data, author_id=user.id)
    return NewsPostResponse.model_validate(post)


@router.patch("/admin/{post_id}", response_model=NewsPostResponse)
async def update_post(
    post_id: uuid.UUID,
    data: NewsPostUpdate,
    db: AsyncDatabase,
    user: User = Depends(fastapi_users.current_user(active=True, superuser=True)),
):
    """Update a news post. Admin only."""
    service = NewsService(db)
    post = await service.update_post(post_id=post_id, data=data)
    return NewsPostResponse.model_validate(post)


@router.delete("/admin/{post_id}", status_code=204)
async def delete_post(
    post_id: uuid.UUID,
    db: AsyncDatabase,
    user: User = Depends(fastapi_users.current_user(active=True, superuser=True)),
):
    """Delete a news post. Admin only."""
    service = NewsService(db)
    await service.delete_post(post_id=post_id)
