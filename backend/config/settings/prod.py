from .base import *

# Static Files + WhiteNoise
STATICFILES_DIRS = [BACKEND_DIR / "frontend_dist"]
WHITENOISE_ROOT = STATICFILES_DIRS[0] / "frontend"

# CSRF
CSRF_TRUSTED_ORIGINS = [f"https://{APP_DOMAIN}"]
