from typing import Any

from app.agent.graph.chains.generation import generation_chain
from app.agent.graph.state import GraphState


async def generate_node(state: GraphState) -> dict[str, Any]:
    question = state["question"]
    documents = state["documents"]

    context_str = "\n".join(documents)
    generation = await generation_chain.ainvoke({
        "context": context_str,
        "question": question,
    })
    return {
        "generation": generation,
    }
