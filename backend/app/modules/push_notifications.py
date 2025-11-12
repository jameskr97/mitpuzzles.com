import uuid
import json
from datetime import datetime
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import String, DateTime, ForeignKey, select, delete
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from pywebpush import webpush, WebPushException
import uuid6

from app.models import Base
from app.dependencies import get_async_session, AsyncSession
from app.config import settings
from app.modules.authentication import fastapi_users, User


# SQLAlchemy Model
class PushSubscription(Base):
    __tablename__ = "push_subscription"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid6.uuid7)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)

    # Push subscription data
    endpoint: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    p256dh_key: Mapped[str] = mapped_column(String, nullable=False)
    auth_key: Mapped[str] = mapped_column(String, nullable=False)

    # Audit fields
    date_created: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)
    date_updated: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


# Pydantic Schemas
class PushSubscriptionCreate(BaseModel):
    endpoint: str
    keys: Dict[str, str]  # Contains p256dh and auth


class PushSubscriptionResponse(BaseModel):
    success: bool
    message: str

    class Config:
        from_attributes = True


class VapidPublicKeyResponse(BaseModel):
    public_key: str


# Router
router = APIRouter(tags=["Push Notifications"], prefix="/api/push")


@router.get("/vapid-public-key", response_model=VapidPublicKeyResponse)
async def get_vapid_public_key():
    """Get the VAPID public key for push subscription"""
    return VapidPublicKeyResponse(public_key=settings.VAPID_PUBLIC_KEY)


@router.post("/subscribe", response_model=PushSubscriptionResponse)
async def subscribe_to_push(
    subscription: PushSubscriptionCreate,
    current_user: User = Depends(fastapi_users.current_user()),
    session: AsyncSession = Depends(get_async_session),
):
    """Subscribe current user to push notifications"""

    # Check if subscription already exists for this endpoint
    stmt = select(PushSubscription).where(PushSubscription.endpoint == subscription.endpoint)
    result = await session.execute(stmt)
    existing_subscription = result.scalar_one_or_none()

    if existing_subscription:
        # Update existing subscription (user might have logged in on different account on same browser)
        existing_subscription.user_id = current_user.id
        existing_subscription.p256dh_key = subscription.keys["p256dh"]
        existing_subscription.auth_key = subscription.keys["auth"]
        existing_subscription.date_updated = datetime.utcnow()
    else:
        # Create new subscription
        new_subscription = PushSubscription(
            user_id=current_user.id,
            endpoint=subscription.endpoint,
            p256dh_key=subscription.keys["p256dh"],
            auth_key=subscription.keys["auth"],
        )
        session.add(new_subscription)

    await session.commit()

    return PushSubscriptionResponse(
        success=True,
        message="Successfully subscribed to push notifications"
    )


@router.delete("/unsubscribe", response_model=PushSubscriptionResponse)
async def unsubscribe_from_push(
    subscription: PushSubscriptionCreate,
    current_user: User = Depends(fastapi_users.current_user()),
    session: AsyncSession = Depends(get_async_session),
):
    """Unsubscribe current user from push notifications"""

    # Delete subscription for this endpoint and user
    stmt = delete(PushSubscription).where(
        PushSubscription.endpoint == subscription.endpoint,
        PushSubscription.user_id == current_user.id
    )
    result = await session.execute(stmt)
    await session.commit()

    if result.rowcount == 0:
        return PushSubscriptionResponse(
            success=False,
            message="No subscription found"
        )

    return PushSubscriptionResponse(
        success=True,
        message="Successfully unsubscribed from push notifications"
    )


@router.get("/subscription-status")
async def get_subscription_status(
    current_user: User | None = Depends(fastapi_users.current_user(optional=True)),
    session: AsyncSession = Depends(get_async_session),
):
    """Check if current user has any push subscriptions"""
    if not current_user:
        return {"subscribed": False}

    # Check if user has any subscriptions
    stmt = select(PushSubscription).where(PushSubscription.user_id == current_user.id).limit(1)
    result = await session.execute(stmt)
    subscription = result.scalar_one_or_none()

    return {"subscribed": subscription is not None}


# Push Notification Service Functions
async def send_push_to_subscription(subscription: PushSubscription, title: str, body: str) -> bool:
    """Send a push notification to a single subscription"""
    try:
        # Prepare the notification payload
        payload = json.dumps({
            "title": title,
            "body": body,
            "icon": "/favicon.svg",
            "badge": "/favicon.svg",
        })

        # Prepare subscription info for pywebpush
        subscription_info = {
            "endpoint": subscription.endpoint,
            "keys": {
                "p256dh": subscription.p256dh_key,
                "auth": subscription.auth_key,
            }
        }

        # Send the push notification
        webpush(
            subscription_info=subscription_info,
            data=payload,
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={
                "sub": f"mailto:{settings.VAPID_CLAIM_EMAIL}"
            }
        )

        return True

    except WebPushException as e:
        print(f"WebPush failed for subscription {subscription.id}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error sending push notification: {e}")
        return False


async def send_push_to_all(session: AsyncSession, title: str, body: str, admin_only: bool = False) -> Dict[str, int]:
    """Send push notification to all subscribed users (or just superusers if admin_only=True)"""
    from app.modules.authentication import User

    if admin_only:
        # Get subscriptions for superusers only
        stmt = (
            select(PushSubscription)
            .join(User, PushSubscription.user_id == User.id)
            .where(User.is_superuser == True)
        )
    else:
        # Get all subscriptions
        stmt = select(PushSubscription)

    result = await session.execute(stmt)
    subscriptions = result.scalars().all()

    success_count = 0
    failed_count = 0

    for subscription in subscriptions:
        success = await send_push_to_subscription(subscription, title, body)
        if success:
            success_count += 1
        else:
            failed_count += 1

    return {
        "sent": success_count,
        "failed": failed_count,
        "total": len(subscriptions)
    }
