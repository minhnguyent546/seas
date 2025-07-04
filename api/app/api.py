from fastapi import APIRouter

from app.auth.routes import router as auth_router
from app.users.routes import router as users_router

api_router = APIRouter()

api_router.include_router(users_router)
api_router.include_router(auth_router)
