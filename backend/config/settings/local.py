from .base import *

# Directory Paths
# FRONTEND_DIR = BACKEND_DIR.parent / "frontend"

# Static Files
# STATICFILES_DIRS = [FRONTEND_DIR / "dist"]

# WhiteNoise
# WHITENOISE_ROOT = FRONTEND_DIR / "dist"

# Vue Frontend Proxy
VUE_FRONTEND_URL = "http://localhost:3000"
CSRF_TRUSTED_ORIGINS = [VUE_FRONTEND_URL]

# Allauth Local Settings
HEADLESS_SERVE_SPECIFICATION = True
