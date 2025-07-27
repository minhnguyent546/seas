from typing import TypedDict


class GraphState(TypedDict):
    question: str
    generation: str
    web_search: bool
    documents: list[
        str
    ]  # each item will be: <Document title="title" url="url">content</Document>
    classification: str  # "yes" or "no" for question relevance
