from enum import Enum
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict


class DeploymentEnvironment(str, Enum):
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    ENVIRONMENT: DeploymentEnvironment = DeploymentEnvironment.LOCAL
    TESTING: bool = False  # Enable test mode (skips emails, exposes test endpoints)

    # domains
    APP_DOMAIN: set[str] = {"mitpuzzles.com"}
    FRONTEND_HOST: str = "http://localhost:3000"

    # database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/mitpuzzles"

    # auth
    SECRET: str = "secret-secret-secret-secret"
    RESEND_API_KEY: str = None
    OAUTH_GOOGLE_CLIENT_ID: str = None
    OAUTH_GOOGLE_CLIENT_SECRET: str = None

    # web push notifications
    VAPID_PUBLIC_KEY: str = None
    VAPID_PRIVATE_KEY: str = None
    VAPID_CLAIM_EMAIL: str = None

    # celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # static files
    STATIC_FILES_PATH: str = "/app/static"
    SERVE_STATIC_FILES: bool = False

    # data exports
    EXPORT_DIR: str = "/app/exports"

    def model_post_init(self, context: Any, /) -> None:
        self.configure_for_environment()

    def configure_for_environment(self):
        """configure settings based on deployment environment"""
        print(f"ENVIRONMENT: {self.ENVIRONMENT}")
        print(f"DATABASE_URL: {self.DATABASE_URL}")
        if self.ENVIRONMENT == DeploymentEnvironment.LOCAL:
            self._configure_local()
        elif self.ENVIRONMENT == DeploymentEnvironment.STAGING:
            self._configure_staging()
        elif self.ENVIRONMENT == DeploymentEnvironment.PRODUCTION:
            self._configure_production()
        print(f"FRONTEND_HOST: {self.FRONTEND_HOST}")


    def _configure_local(self):
        """local development configuration"""
        print("Configuring for local development")
        self.APP_DOMAIN = {"localhost:3000", "127.0.0.1:3000"}
        self.FRONTEND_HOST = "http://localhost:3000"
        self.SERVE_STATIC_FILES = False
        self.EXPORT_DIR = ".exports"

    def _configure_staging(self):
        """staging environment configuration"""
        print("Configuring for staging")
        self.APP_DOMAIN = {"staging.mitpuzzles.com"}
        self.FRONTEND_HOST = "https://staging.mitpuzzles.com"
        self.SERVE_STATIC_FILES = True
        self.STATIC_FILES_PATH = "/app/static"

    def _configure_production(self):
        """production environment configuration"""
        print("Configuring for production")
        self.APP_DOMAIN = {"mitpuzzles.com"}
        self.FRONTEND_HOST = "https://mitpuzzles.com"
        self.SERVE_STATIC_FILES = True
        self.STATIC_FILES_PATH = "/app/static"


settings = Settings()
