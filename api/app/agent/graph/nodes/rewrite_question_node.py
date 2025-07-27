from typing import Any

from loguru import logger

from app.agent.graph.chains import rewrite_question_chain
from app.agent.graph.state import GraphState


async def rewrite_question_node(state: GraphState) -> dict[str, Any]:
    question = state["question"]
    rewritten_question = await rewrite_question_chain.ainvoke({
        "question": question
    })  # pyright: ignore[reportAssignmentType]
    logger.debug(f"{rewritten_question = }")
    return {"question": rewritten_question}
