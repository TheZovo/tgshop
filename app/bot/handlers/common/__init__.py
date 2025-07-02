from aiogram import Router
from .start import router as start_router
from .profile import router as profile_router
from .topup import router as topup_router

router = Router()
router.include_router(start_router)
router.include_router(profile_router)
router.include_router(topup_router)