from html import escape as html_escape
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


class DocumentTag(BaseModel):
    title: str
    url: str
    description: str
    content: str

    def to_html(self) -> str:
        return f'<Document title="{html_escape(self.title)}" url="{html_escape(self.url)}" description="{html_escape(self.description)}">{html_escape(self.content)}</Document>'
