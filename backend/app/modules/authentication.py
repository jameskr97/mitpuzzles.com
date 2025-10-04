from fastapi_users.db import SQLAlchemyUserDatabase, SQLAlchemyBaseOAuthAccountTableUUID  # this one must be imported first?
from fastapi_users_db_sqlalchemy.access_token import SQLAlchemyBaseAccessTokenTableUUID, SQLAlchemyAccessTokenDatabase
from fastapi_users.authentication.strategy.db import AccessTokenDatabase, DatabaseStrategy
from fastapi_users import schemas, models
from sqlalchemy import String, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column

from httpx_oauth.clients.google import GoogleOAuth2
from fastapi_users.authentication import CookieTransport, AuthenticationBackend
from fastapi_users import BaseUserManager, UUIDIDMixin, FastAPIUsers
from fastapi import Depends, Request, APIRouter, Response

from app.dependencies import get_async_session, AsyncSession
from app.service.email import send_verification_email
from app.models import Base
from app.config import settings

from typing import Optional
import datetime
import uuid
import uuid6

AUTH_SESSION_TIME = 3600 * 24 * 30 # stay logged in for 30 days

# Schemas
class UserRead(schemas.BaseUser[uuid.UUID]):
    username: Optional[str]


class UserUpdate(schemas.BaseUserUpdate):
    username: Optional[str] = None


class UserCreate(schemas.BaseUserCreate):
    username: Optional[str] = None


# Models
class OAuthAccount(SQLAlchemyBaseOAuthAccountTableUUID, Base):
    __tablename__ = "user_oauth_accounts"


class AccessToken(SQLAlchemyBaseAccessTokenTableUUID, Base):
    __tablename__ = "user_accesstoken"


class User(Base):
    __tablename__ = "user"
    # id + audit
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid6.uuid7)
    date_created: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.utcnow, nullable=False)
    date_updated: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    # users fields
    username: Mapped[Optional[str]] = mapped_column(String(length=50), unique=True, nullable=True)
    email: Mapped[str] = mapped_column(String(length=320), unique=True, index=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(length=1024), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # relationships
    oauth_accounts: Mapped[list[OAuthAccount]] = relationship("OAuthAccount", lazy="joined")


# Services
async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User, OAuthAccount)


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)


async def get_access_token_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyAccessTokenDatabase(session, AccessToken)


def get_database_strategy(access_token_db: AccessTokenDatabase[AccessToken] = Depends(get_access_token_db)) -> DatabaseStrategy:
    return DatabaseStrategy(access_token_db, lifetime_seconds=AUTH_SESSION_TIME)


cookie_transport = CookieTransport(
    cookie_name="access_token",
    cookie_max_age=AUTH_SESSION_TIME, # stay logged in for one year
)
auth_backend = AuthenticationBackend(name="cookie", transport=cookie_transport, get_strategy=get_database_strategy)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.SECRET
    verification_token_secret = settings.SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print("User registered:", user.id, user.email)
        if not user.is_verified:
            await self.request_verify(user)

    async def on_after_request_verify(self, user: User, token: str, request: Optional[Request] = None):
        await send_verification_email(user.email, token)

    async def on_after_login(
        self,
        user: models.UP,
        request: Optional[Request] = None,
        response: Optional[Response] = None,
    ) -> None:
        if response:
            response.status_code = 303
            response.headers["Location"] = settings.FRONTEND_HOST

    async def update(
        self,
        user_update: schemas.BaseUserUpdate,
        user: models.UP,
        safe: bool = False,
        request: Optional[Request] = None,
    ) -> models.UP:
        if hasattr(user_update, "username") and user_update.username is not None:
            from sqlalchemy import select
            from fastapi import HTTPException

            # check if username belongs to another user
            statement = select(User).where(User.username == user_update.username, User.id != user.id)
            result = await self.user_db.session.execute(statement)
            existing_user = result.unique().scalar_one_or_none()

            if existing_user:
                raise HTTPException(status_code=400, detail="Username already exists")

        return await super().update(user_update, user, safe=safe, request=request)


# Routers
fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])
oauth_google = GoogleOAuth2(client_id=settings.OAUTH_GOOGLE_CLIENT_ID, client_secret=settings.OAUTH_GOOGLE_CLIENT_SECRET)

router_auth = APIRouter(tags=["Authentication"])
router_auth.include_router(prefix="/api/auth", router=fastapi_users.get_register_router(UserRead, UserCreate))
router_auth.include_router(prefix="/api/auth", router=fastapi_users.get_auth_router(auth_backend))
router_auth.include_router(prefix="/api/auth", router=fastapi_users.get_verify_router(UserRead))
router_auth.include_router(
    prefix="/api/oauth/google",
    router=fastapi_users.get_oauth_router(
        oauth_google, auth_backend, settings.SECRET, is_verified_by_default=True, redirect_url=f"{settings.FRONTEND_HOST}/api/oauth/google/callback"
    ),
)

router_user = APIRouter(tags=["Users"])
router_user.include_router(prefix="/api/users", router=fastapi_users.get_users_router(UserRead, UserUpdate, requires_verification=True))
