from .base import *

# Static Files + WhiteNoise
STATICFILES_DIRS = [BACKEND_DIR / "frontend_dist"]
WHITENOISE_ROOT = "frontend_dist"
