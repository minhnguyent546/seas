from fastapi import APIRouter

from app.auth.routes import router as auth_router
from app.chatbot.routes import router as chatbot_router
from app.chats.routes import router as chats_router
from app.rag.routes import router as rag_router
from app.users.routes import router as users_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(chats_router)
api_router.include_router(chatbot_router)
api_router.include_router(rag_router)
