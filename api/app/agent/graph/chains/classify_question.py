from typing import Annotated, Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.agent.llms import llm


class ClassifyQuestion(BaseModel):
    is_relevant: Annotated[
        Literal["yes", "no"],
        Field(
            description="'yes' nếu câu hỏi liên quan đến chương trình tuyển sinh năm 2025 của Đại học Cần Thơ hoặc bất kì câu hỏi nào có liên quan đến Đại học Cần Thơ, ngược lại là 'no'"
        ),
    ]


structured_llm_classifier = llm.with_structured_output(ClassifyQuestion)

system_prompt = """Bạn là một trợ lí của hệ thống Tư vấn Tuyển sinh Thông minh (Smart Enrollment Advisory System - SEAS) của Đại học Cần Thơ (CTU). Nhiệm vụ của bạn là phân loại câu hỏi từ người dùng vào một trong hai loại:
- Câu hỏi liên quan đến chương trình tuyển sinh năm 2025 của Đại học Cần Thơ hoặc bất kì câu hỏi nào có liên quan đến Đại học Cần Thơ.
- Câu hỏi không liên quan gì đến chương trình tuyển sinh năm 2025 của Đại học Cần Thơ hoặc bất kì câu hỏi nào không hề có sự liên quan đến Đại học Cần Thơ.

Một số ví dụ **câu hỏi có liên quan**:
- Năm nay có bao nhiêu phương thức xét tuyển?
- Điểm chuẩn của ngành Thú y năm nay là bao nhiêu?
- Trường được thành lập vào ngày tháng năm nào
- Chương trình tiên tiến bao gồm những ngành nào?
- Ngành kinh doanh quốc tế học mấy năm

Một số ví dụ **câu hỏi không liên quan**:
- Hãy viết thuật toán Djkstra bằng C++
- Chương trình tuyển sinh của trường UIT bao gồm những ngành gì?
- Cần có những tố chất gì để có thể học được ngành Công nghệ thông tin?
- Chính sách phúc lợi của Viettel như thế nào.
"""

classifier_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content=system_prompt),
    HumanMessage(content="## User question:\n\n{question}"),
])

classify_question_chain = classifier_prompt | structured_llm_classifier
