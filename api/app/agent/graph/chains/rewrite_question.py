
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger
from pydantic import BaseModel, Field

from app.agent.llms import llm

# class RewriteQuestion(BaseModel):
#     rewritten_question: str = Field(..., description="Rewritten question to be used for retrieval.")


# structured_llm_rewriter = llm.with_structured_output(RewriteQuestion)

system_prompt = "You are a query rewriter that reformulates the user question for document retrieval. Return only the rewritten question."


class Rewrite(BaseModel):
    rewritten: str = Field(..., description="The reformulated query")


parser = PydanticOutputParser(pydantic_object=Rewrite)
instr = parser.get_format_instructions()

rewrite_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content=system_prompt),
    HumanMessage(content="{instructions}\nOriginal: {question}\nResult:"),
]).partial(instructions=instr)


# rewrite_prompt = ChatPromptTemplate.from_messages([
#     SystemMessage(content=system_prompt),
#     HumanMessage(content="## User question:\n\n{question}\n\n## Rewritten question:\n\n")
# ])

rewrite_question_chain = rewrite_prompt | llm | StrOutputParser()
