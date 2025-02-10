from .base import *

# Static Files
STATICFILES_DIRS = [FRONTEND_DIR / "dist"]

# WhiteNoise
WHITENOISE_ROOT = FRONTEND_DIR / "dist"
WHITENOISE_INDEX_FILE = "index.html"

# Vue Frontend Proxy
CSRF_TRUSTED_ORIGINS = ["http://localhost:3000"]