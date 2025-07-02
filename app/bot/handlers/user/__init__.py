from aiogram import Router
from .purchases import router as purchases_router
from .shop import router as shop_router

router = Router()
router.include_router(purchases_router)
router.include_router(shop_router)