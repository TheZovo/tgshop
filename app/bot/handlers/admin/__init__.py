from aiogram import Router
from .logs import router as logs_router
from .menu import router as menu_router
from .products import router as products_router
from .promocodes import router as promocodes_router
from .users import router as users_router

router = Router()
router.include_router(menu_router)
router.include_router(logs_router)
router.include_router(products_router)
router.include_router(promocodes_router)
router.include_router(users_router)