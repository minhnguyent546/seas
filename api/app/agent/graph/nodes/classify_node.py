from typing import Any

from loguru import logger

from app.agent.graph.chains.classify_question import (
    ClassifyQuestion,
    classify_question_chain,
)
from app.agent.graph.consts import REJECT, RETRIEVE
from app.agent.graph.state import GraphState


async def classify_node(state: GraphState) -> dict[str, Any]:
    """
    Classify the user question to determine if it's relevant to CTU admission.

    Args:
        state: The current graph state containing the question

    Returns:
        Updated state with classification result
    """
    question = state["question"]
    result: ClassifyQuestion = await classify_question_chain.ainvoke({
        "question": question
    })  # pyright: ignore[reportAssignmentType]
    logger.debug(f"classification result = {result}")

    # Store the classification result in state
    return {
        "classification": result.is_relevant,
    }


def classify_user_question_router(state: GraphState) -> str:
    """
    Route based on classification result.

    Args:
        state: The current graph state

    Returns:
        Next node name based on classification
    """
    classification = state.get("classification", "yes")
    logger.debug(f"in classify router: {classification = }")
    if classification == "yes":
        return RETRIEVE
    else:
        return REJECT
