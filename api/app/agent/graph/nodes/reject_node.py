from typing import Any

from app.agent.graph.state import GraphState


async def reject_node(state: GraphState) -> dict[str, Any]:
    rejection_message = """Xin lỗi, dường như câu hỏi của bạn không liên quan đến chương trình tuyển sinh năm 2025 của Đại học Cần Thơ hoặc có liên quan đến Đại học Cần Thơ."""

    return {"generation": rejection_message}
