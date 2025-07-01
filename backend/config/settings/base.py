# This file is used to configure the Django settings for the project.
# The "base.py", "local.py", "prod.py" define settings for their respective environments.
#   - "base.py"     contains base settings applied to all environments.
#   - "local.py"    contains overrides when running the project locally (this is the default environment).
#   - "prod.py"     contains overrides when running the project in a production environment.
# Documentation Links:
# - https://docs.djangoproject.com/en/5.1/topics/settings/
# - https://docs.djangoproject.com/en/5.1/ref/settings/
# - https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/
# - https://docs.djangoproject.com/en/5.1/ref/settings/#databases
import os
from pathlib import Path

import environ

# Directory Paths
BACKEND_DIR = Path(os.path.abspath(__file__)).parent.parent.parent

# App Specific Settings
env = environ.FileAwareEnv(
    DEBUG=(bool, True),
    SECRET_KEY=(str, "unsafe-secret-key-dont-use-in-production"),
    # App Specific
    APP_DOMAIN=(str, "localhost"),
    DATABASE_URL=(str, "postgres://mitlogic:mitlogic@localhost:5432/mitlogic"),
    REDIS_HOST=(str, "localhost"),
    REDIS_PORT=(int, 6379),
)
environ.Env.read_env(BACKEND_DIR / ".env")

# Load Environment Variables
APP_DOMAIN = env("APP_DOMAIN")
DEBUG = env("DEBUG")
SECRET_KEY = env("SECRET_KEY")
DATABASES = {"default": env.db("DATABASE_URL")}
REDIS_DB = (env("REDIS_HOST"), env("REDIS_PORT"))

# Essential Django settings
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ALLOWED_HOSTS = [APP_DOMAIN]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"  # Django default for auto incrementing primary keys
AUTH_USER_MODEL = "accounts.User"
ASGI_APPLICATION = "config.asgi.application"

## Static Files
STATIC_URL = "/static/"
STATIC_ROOT = "staticfiles"
WHITENOISE_INDEX_FILE = True

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/New_York"
USE_I18N = True
USE_TZ = True

# Session Settings
# SESSION_COOKIE_AGE = 86400 * 365 * 2 # 2 years
SESSION_COOKIE_AGE = 86400 * 365  # 2 weeks

# Django App + Middleware Settings
INSTALLED_APPS = [
    # Django Default Apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 3rd-Party Apps
    "allauth.account",
    "allauth.headless",
    "rest_framework",
    "django_json_widget",
    # Local Apps
    "core",
    "accounts",
    "tracking",
    "puzzles",
    "experiments",
    # "protocol"
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "tracking.middleware.VisitorMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # must be below SecurityMiddleware
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Allauth
    "allauth.account.middleware.AccountMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BACKEND_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

# Password Validation (https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators)
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# allauth config
HEADLESS_ONLY = True  # disable allauth's default views, we'll use the vue frontend
HEADLESS_ADAPTER = "accounts.adapter.CustomHeadlessAdapter"
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

HEADLESS_FRONTEND_URLS = {
    "account_confirm_email": f"https://{APP_DOMAIN}/account/verify-email/{{key}}",
    "account_reset_password_from_key": f"https://{APP_DOMAIN}/account/password/reset/key/{{key}}",
    "account_signup": f"https://{APP_DOMAIN}/account/signup",
}

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_LOGIN_METHODS = ["email"]

# django channels
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_DB],
        },
    },
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'colored': {
            '()': 'colorlog.ColoredFormatter',
            'format': '%(log_color)s[%(levelname)s]%(reset)s %(asctime)s %(name)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'log_colors': {
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            },
        },
        'detailed_colored': {
            '()': 'colorlog.ColoredFormatter',
            'format': '%(log_color)s[%(levelname)s]%(reset)s %(asctime)s %(purple)s%(name)s%(reset)s:%(blue)s%(lineno)d%(reset)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'log_colors': {
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            },
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'colored',
        },
        'detailed_console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'detailed_colored',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django.server': {
            "handlers": ['console'],
            "level": "INFO",
            "propagate": False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.channels': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'daphne': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        # Your app loggers
        'puzzles': {
            'handlers': ['detailed_console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
