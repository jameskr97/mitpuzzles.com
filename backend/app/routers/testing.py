"""
Test-only endpoints for Playwright E2E testing.
These endpoints are only available when TESTING=true.
"""
import secrets

import uuid6
from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel
from sqlalchemy import select

from app.service.email import get_test_verification_token, get_test_reset_token
from app.dependencies import get_async_session, AsyncSession
from app.modules.authentication import User, OAuthAccount, AccessToken, AUTH_SESSION_TIME


router = APIRouter(prefix="/api/test", tags=["Testing"])


class OAuthLoginRequest(BaseModel):
    email: str


@router.get("/verification-token/{email}")
async def get_verification_token(email: str):
    """Get the verification token for an email (test mode only)"""
    token = get_test_verification_token(email)
    if not token:
        raise HTTPException(status_code=404, detail="No verification token found for this email")
    return {"token": token}


@router.get("/reset-token/{email}")
async def get_reset_token(email: str):
    """Get the password reset token for an email (test mode only)"""
    token = get_test_reset_token(email)
    if not token:
        raise HTTPException(status_code=404, detail="No reset token found for this email")
    return {"token": token}


@router.post("/oauth-login")
async def test_oauth_login(
    request: OAuthLoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_async_session),
):
    """Create or get an OAuth-linked user and log them in (test mode only)"""
    email = request.email

    # Check if user exists
    result = await session.execute(select(User).where(User.email == email))
    user = result.unique().scalar_one_or_none()

    if not user:
        # Create new user (OAuth users are verified by default, no real password needed)
        user = User(
            id=uuid6.uuid7(),
            email=email,
            hashed_password=secrets.token_hex(32),  # Random password since OAuth doesn't use it
            is_verified=True,
            is_active=True,
            is_superuser=False,
        )
        session.add(user)
        await session.flush()

        # Create OAuth account link
        oauth_account = OAuthAccount(
            oauth_name="google",
            access_token="test_access_token",
            account_id=f"test_{secrets.token_hex(8)}",
            account_email=email,
            user_id=user.id,
        )
        session.add(oauth_account)

    # Create access token for session
    access_token = AccessToken(
        token=secrets.token_urlsafe(32),
        user_id=user.id,
    )
    session.add(access_token)
    await session.commit()

    # Set the session cookie (match CookieTransport settings)
    response.set_cookie(
        key="access_token",
        value=access_token.token,
        max_age=AUTH_SESSION_TIME,
        httponly=True,
        secure=False,  # Local testing doesn't use HTTPS
        samesite="lax",
    )

    return {
        "id": str(user.id),
        "email": user.email,
        "is_verified": user.is_verified,
    }
