"""puzzle routes — assembled from domain-specific sub-routers."""

from fastapi import APIRouter

from app.modules.puzzle.routes.freeplay import router as freeplay_router
from app.modules.puzzle.routes.daily import router as daily_router
from app.modules.puzzle.routes.admin import router as admin_router

router = APIRouter(prefix="/api/puzzle", tags=["Puzzles"])
router.include_router(freeplay_router)
router.include_router(daily_router)
router.include_router(admin_router)
