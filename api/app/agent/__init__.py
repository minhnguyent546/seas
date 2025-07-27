from app.agent.graph.graph import generate_graph
from app.agent.graph.state import GraphState

workflow = generate_graph()

agent = workflow.compile()

__all__ = [
    "agent",
    "GraphState",
]
