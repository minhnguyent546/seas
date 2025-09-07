from typing import Annotated

from pydantic import BaseModel, Field


class TokenData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: float  # in seconds


class NewPassword(BaseModel):
    token: str
    new_password: Annotated[str, Field(min_length=6, max_length=128)]
