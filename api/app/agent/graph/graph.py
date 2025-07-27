
from langgraph.graph import END, START, StateGraph

from app.agent.graph.consts import (
    CLASSIFY,
    GENERATE,
    REJECT,
    RETRIEVE,
    REWRITE_QUESTION,
    WEBSEARCH,
)
from app.agent.graph.nodes import (
    classify_node,
    generate_node,
    reject_node,
    retrieve_node,
    rewrite_question_node,
)
from app.agent.graph.nodes.classify_node import classify_user_question_router
from app.agent.graph.state import GraphState


async def decide_to_generate(state: GraphState):
    if state["web_search"]:
        return WEBSEARCH
    else:
        return GENERATE


def generate_graph():
    workflow = StateGraph(GraphState)

    # Add all nodes
    workflow.add_node(CLASSIFY, classify_node)
    workflow.add_node(REWRITE_QUESTION, rewrite_question_node)
    workflow.add_node(RETRIEVE, retrieve_node)
    workflow.add_node(GENERATE, generate_node)
    workflow.add_node(REJECT, reject_node)

    # Start with classification
    workflow.add_edge(START, CLASSIFY)

    # Route based on classification result
    workflow.add_conditional_edges(
        CLASSIFY,
        classify_user_question_router,
        {
            RETRIEVE: REWRITE_QUESTION,
            REJECT: REJECT,
        },
    )

    # Continue with the rest of the flow
    workflow.add_edge(REWRITE_QUESTION, RETRIEVE)
    workflow.add_edge(RETRIEVE, GENERATE)
    workflow.add_edge(GENERATE, END)
    workflow.add_edge(REJECT, END)

    return workflow


if __name__ == "__main__":
    workflow = generate_graph()

    app = workflow.compile()
    app.get_graph().draw_mermaid_png(output_file_path="graph.png")
