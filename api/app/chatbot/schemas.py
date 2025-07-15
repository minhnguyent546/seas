from pydantic import BaseModel


class ChatQuery(BaseModel):
    query: str
