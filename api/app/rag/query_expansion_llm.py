import time
from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

import app.utils as app_utils
from app.core.config import settings


class QueryExpansionLLM:
    def __init__(self, num_new_queries: int):
        self.llm = app_utils.get_langchain_llm(
            model_name=settings.QUERY_EXPANSION_MODEL,
            temperature=0.6,
        )
        self.num_new_queries = num_new_queries

        self.system_prompt = app_utils.get_prompt(
            template_name="query_expansion_system_prompt.j2",
            currentDateTime=datetime.now().strftime("ngày %d tháng %m năm %Y"),
            currentYear=datetime.now().year,
            numNewQueries=num_new_queries,
        )
        self.human_prompt_template = app_utils.get_prompt_template(
            template_name="query_expansion_human_prompt.j2"
        )

    async def enhance_query(self, query: str) -> str:
        """Enhance query by rewriting it to be more specific and detailed."""
        raise NotImplementedError("Not implemented")

    async def expand_query(self, query: str) -> list[str]:
        """Expand query by creating new queries that are similar to the original query."""
        _start_time = time.perf_counter()

        human_prompt = self.human_prompt_template.render(query=query)
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=human_prompt),
        ]
        response = await self.llm.ainvoke(input=messages)
        response_content = response.content

        elapsed_time = time.perf_counter() - _start_time
        logger.debug(
            f"Query expansion: {elapsed_time:.2f} seconds for expanding {self.num_new_queries} queries"
        )

        assert isinstance(response_content, str)
        if "IRRELEVANT" in response_content:
            return []

        new_queries: list[str] = [
            line.strip()
            for line in response_content.split("\n")
            if line.strip()
        ]
        return new_queries
