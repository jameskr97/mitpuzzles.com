from fastapi_users.db import SQLAlchemyUserDatabase, SQLAlchemyBaseOAuthAccountTableUUID  # this one must be imported first?
from fastapi_users_db_sqlalchemy.access_token import SQLAlchemyBaseAccessTokenTableUUID, SQLAlchemyAccessTokenDatabase
from fastapi_users.authentication.strategy.db import AccessTokenDatabase, DatabaseStrategy
from fastapi_users import schemas, models
from sqlalchemy import String, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column

from httpx_oauth.clients.google import GoogleOAuth2
from fastapi_users.authentication import CookieTransport, AuthenticationBackend
from fastapi_users import BaseUserManager, UUIDIDMixin, FastAPIUsers
from fastapi import Depends, Request, APIRouter, Response, HTTPException
from fastapi.responses import JSONResponse

from app.dependencies import get_async_session, AsyncSession
from app.service.email import send_verification_email
from app.models import Base
from app.config import settings, DeploymentEnvironment

from typing import Optional, Dict, Union
import datetime
import uuid
import uuid6
from collections import defaultdict
from datetime import datetime, timedelta
from better_profanity import profanity

AUTH_SESSION_TIME = 3600 * 24 * 30 # stay logged in for 30 days

# Rate limiting for email verification resends
VERIFICATION_RATE_LIMIT = 3  # max requests per hour
VERIFICATION_RATE_WINDOW = 3600  # 1 hour in seconds
verification_requests: Dict[str, list] = defaultdict(list) # TODO(james): use redis?

# Schemas
class UserRead(schemas.BaseUser[uuid.UUID]):
    username: Optional[str]


class UserUpdate(schemas.BaseUserUpdate):
    username: Optional[str] = None
    password: Optional[str] = None
    current_password: Optional[str] = None


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
    date_created: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    date_updated: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # users fields
    username: Mapped[Optional[str]] = mapped_column(String(length=50), unique=True, nullable=True)
    email: Mapped[str] = mapped_column(String(length=320), unique=True, index=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(length=1024), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # relationships
    oauth_accounts: Mapped[list[OAuthAccount]] = relationship("OAuthAccount", lazy="joined")
    # profile: Mapped[Optional["UserProfile"]] = relationship("UserProfile", back_populates="user", uselist=False, lazy="joined")


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
    cookie_max_age=AUTH_SESSION_TIME,  # stay logged in for 30 days
    cookie_secure=settings.ENVIRONMENT != DeploymentEnvironment.LOCAL,  # Only require HTTPS in non-local
    cookie_samesite="lax",
)
auth_backend = AuthenticationBackend(name="cookie", transport=cookie_transport, get_strategy=get_database_strategy)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.SECRET
    verification_token_secret = settings.SECRET

    async def validate_password(
        self,
        password: str,
        user: Union[UserCreate, User],
    ) -> None:
        # validate password using parent class
        await super().validate_password(password, user)

        # check if username already exists (only during registration)
        if isinstance(user, UserCreate) and hasattr(user, "username") and user.username is not None:
            from sqlalchemy import select

            # check for profanity in username
            if profanity.contains_profanity(user.username):
                raise HTTPException(status_code=400, detail="Username contains inappropriate language")

            statement = select(User).where(User.username == user.username)
            result = await self.user_db.session.execute(statement)
            existing_user = result.unique().scalar_one_or_none()

            if existing_user:
                raise HTTPException(status_code=400, detail="USERNAME_ALREADY_EXISTS")

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        if not user.is_verified:
            await self.request_verify(user)

        # Auto-login the user after registration
        if request and hasattr(request, 'state'):
            request.state.auto_login_user = user

    async def on_after_request_verify(self, user: User, token: str, request: Optional[Request] = None):
        await send_verification_email(user.email, token)

    async def on_after_forgot_password(self, user: User, token: str, request: Optional[Request] = None):
        from app.service.email import send_password_reset_email
        await send_password_reset_email(user.email, token)

    async def on_after_login(
        self,
        user: models.UP,
        request: Optional[Request] = None,
        response: Optional[Response] = None,
    ) -> None:
        # only redirect for oauth logins (check if request came from oauth callback)
        if request and "/oauth/" in str(request.url.path):
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

            # check for profanity in username
            if profanity.contains_profanity(user_update.username):
                raise HTTPException(status_code=400, detail="Username contains inappropriate language")

            # check if username belongs to another user
            statement = select(User).where(User.username == user_update.username, User.id != user.id)
            result = await self.user_db.session.execute(statement)
            existing_user = result.unique().scalar_one_or_none()

            if existing_user:
                raise HTTPException(status_code=400, detail="Username already exists")

        # handle password update with current password verification
        if hasattr(user_update, "password") and user_update.password is not None:
            from fastapi import HTTPException

            # require current password for password changes
            if not hasattr(user_update, "current_password") or not user_update.current_password:
                raise HTTPException(status_code=400, detail="Current password is required to change password")

            # verify current password
            valid_password = self.password_helper.verify_and_update(
                user_update.current_password, user.hashed_password
            )
            if not valid_password[0]:
                raise HTTPException(status_code=400, detail="Current password is incorrect")

            # validate new password
            await self.validate_password(user_update.password, user)

        return await super().update(user_update, user, safe=safe, request=request)


# Routers
fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])
oauth_google = GoogleOAuth2(client_id=settings.OAUTH_GOOGLE_CLIENT_ID, client_secret=settings.OAUTH_GOOGLE_CLIENT_SECRET)

router_auth = APIRouter(tags=["Authentication"])
router_auth.include_router(prefix="/api/auth", router=fastapi_users.get_register_router(UserRead, UserCreate))
router_auth.include_router(prefix="/api/auth", router=fastapi_users.get_auth_router(auth_backend))

# get verify router and remove the default /request-verify-token route
verify_router = fastapi_users.get_verify_router(UserRead)
verify_router.routes = [route for route in verify_router.routes if not (hasattr(route, 'path') and route.path == '/request-verify-token')]

router_auth.include_router(prefix="/api/auth", router=verify_router)
router_auth.include_router(prefix="/api/auth", router=fastapi_users.get_reset_password_router())
router_auth.include_router(
    prefix="/api/oauth/google",
    router=fastapi_users.get_oauth_router(
        oauth_google, auth_backend, settings.SECRET, is_verified_by_default=True, redirect_url=f"{settings.FRONTEND_HOST}/api/oauth/google/callback"
    ),
)

# rate limiting helper function
def check_verification_rate_limit(user_id: str) -> bool:
    now = datetime.now()
    user_requests = verification_requests[user_id]
    # remove old requests outside the window
    cutoff_time = now - timedelta(seconds=VERIFICATION_RATE_WINDOW)
    verification_requests[user_id] = [req_time for req_time in user_requests if req_time > cutoff_time]
    return len(verification_requests[user_id]) < VERIFICATION_RATE_LIMIT

# Resend verification email endpoint
@router_auth.post("/api/auth/request-verify-token")
async def resend_verification_email(
    user: User = Depends(fastapi_users.current_user()),
    user_manager: UserManager = Depends(get_user_manager)
):
    """Resend verification email with rate limiting"""
    if user.is_verified:
        raise HTTPException(status_code=400, detail="User already verified")

    user_id_str = str(user.id)
    if not check_verification_rate_limit(user_id_str):
        raise HTTPException(
            status_code=429,
            detail="Too many verification requests. Please wait before requesting again."
        )

    verification_requests[user_id_str].append(datetime.now())
    await user_manager.request_verify(user)
    return JSONResponse({"message": "Verification email sent"})

router_user = APIRouter(tags=["Users"])
router_user.include_router(prefix="/api/users", router=fastapi_users.get_users_router(UserRead, UserUpdate, requires_verification=False))
