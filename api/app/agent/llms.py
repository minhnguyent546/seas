import app.utils as app_utils
from app.core.config import settings

llm = app_utils.get_langchain_llm(
    model_name=settings.CHAT_MODEL,
    temperature=0,
)
