from typing import Annotated

from pydantic import BaseModel, Field


class ChatQuery(BaseModel):
    query: Annotated[
        str,
        Field(
            min_length=1,
            max_length=2048,
            examples=["How do I apply for scholarships?"],
        ),
    ]
