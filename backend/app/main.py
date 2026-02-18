import logging
import asyncio
from contextlib import asynccontextmanager
from httpx_oauth.integrations.fastapi import OAuth2AuthorizeCallbackError
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from fastapi import Request, Response
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware

from app.modules import authentication, tracking, feedback, experiments, puzzle, tracking_analytics, user_profile, push_notifications, puzzle_analysis, data_export
from app.config import settings, DeploymentEnvironment
from app.dependencies import async_session_maker

logger = logging.getLogger(__name__)
uvicorn_logger = logging.getLogger("uvicorn")


async def _check_database_connection():
    """check if database is accessible"""
    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
        return True, "database connection successful"
    except SQLAlchemyError as e:
        return False, f"database connection failed: {str(e)}"
    except Exception as e:
        return False, f"unexpected database error: {str(e)}"


async def _check_required_tables():
    """check if required database tables exist"""
    required_tables = ["puzzle", "device", "user", "feedback", "experiment_run", "session_activity"]
    try:
        async with async_session_maker() as session:
            result = await session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            existing_tables = {row[0] for row in result.fetchall()}

            missing_tables = [table for table in required_tables if table not in existing_tables]
            if missing_tables:
                return False, f"missing tables: {', '.join(missing_tables)}"
            return True, f"all required tables exist ({len(required_tables)} tables)"
    except Exception as e:
        return False, f"failed to check tables: {str(e)}"

def _check_environment_config():
    """check environment configuration"""
    issues = []

    if settings.ENVIRONMENT.value == "production":
        if settings.SECRET == "secret-secret-secret-secret":
            issues.append("using default secret in production")
        if not settings.RESEND_API_KEY:
            issues.append("resend api key not configured")
        if not settings.OAUTH_GOOGLE_CLIENT_ID:
            issues.append("google oauth client id not configured")

    if issues:
        return False, f"configuration issues: {'; '.join(issues)}"

    return True, f"environment: {settings.ENVIRONMENT.value}"


async def run_pre_start_checks():
    """run all pre-start checks and exit if any fail"""
    uvicorn_logger.info("🔍 running pre-start checks...")
    checks = [
        ("environment config", _check_environment_config),
        ("database connection", _check_database_connection),
        ("required tables", _check_required_tables),
    ]

    all_passed = True

    for check_name, check_func in checks:
        try:
            if asyncio.iscoroutinefunction(check_func):
                success, message = await check_func()
            else:
                success, message = check_func()

            if success:
                uvicorn_logger.info("✅ %s: %s", check_name, message)
            else:
                uvicorn_logger.error("❌ %s: %s", check_name, message)
                all_passed = False

        except Exception as e:
            uvicorn_logger.error("❌ %s: check failed with error: %s", check_name, str(e))
            all_passed = False

    if not all_passed:
        uvicorn_logger.error("❌ pre-start checks failed. please fix the issues above before starting the server.")
        raise SystemExit

    uvicorn_logger.info("✅ all pre-start checks passed!")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    await run_pre_start_checks()
    yield
    # shutdown (nothing needed for now)


app = FastAPI(
    title="mitpuzzles.com",
    contact={
        "name": "James",
        "email": "support@mitpuzzles.com",
    },
    docs_url="/api/docs" if settings.ENVIRONMENT != DeploymentEnvironment.PRODUCTION else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT != DeploymentEnvironment.PRODUCTION else None,
    lifespan=lifespan,
)
app.include_router(tracking.router)
app.include_router(authentication.router_auth)
app.include_router(authentication.router_user)
app.include_router(user_profile.router_profile)
app.include_router(push_notifications.router)
app.include_router(feedback.router)
app.include_router(experiments.router)
app.include_router(puzzle.router)
app.include_router(tracking_analytics.router)
app.include_router(puzzle_analysis.router)
app.include_router(data_export.router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=[settings.FRONTEND_HOST] if settings.ENVIRONMENT.value == "local" else list(settings.APP_DOMAIN),
    allow_methods=["*"],
    allow_headers=["*"],
)

# add middleware to handle x-forwarded-for from reverse proxy


class proxy_headers_middleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # get real client ip from x-forwarded-for header
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # x-forwarded-for can contain multiple ips, take the first one
            client_ip = forwarded_for.split(",")[0].strip()
            # override the client host with the real ip
            request.scope["client"] = (client_ip, request.client.port if request.client else 0)

        response = await call_next(request)
        return response


app.add_middleware(proxy_headers_middleware)


@app.exception_handler(OAuth2AuthorizeCallbackError)
async def oauth2_authorize_callback_error_handler(request: Request, exc: OAuth2AuthorizeCallbackError):
    detail = exc.detail
    status_code = exc.status_code
    return Response(
        status_code=status_code,
        content={"message": "The OAuth2 callback failed", "detail": detail},
    )


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}


# Test-only endpoints (only available when TESTING=true)
if settings.TESTING:
    from app.routers import testing
    app.include_router(testing.router)


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0")
