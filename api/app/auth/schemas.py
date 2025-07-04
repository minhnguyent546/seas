from typing import Annotated

from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    sub: str | None = None  # store user id


class NewPassword(BaseModel):
    token: str
    new_password: Annotated[str, Field(min_length=6, max_length=128)]
