# agents/rag_agent.py
from langgraph.prebuilt import create_react_agent
from core.llm import get_llm
from memory.memory import memory
from tools.rag_tool import search_docs
from core.logger import get_logger

logger = get_logger("rag_agent")

llm = get_llm()

agent = create_react_agent(
    llm,
    tools=[search_docs],
    checkpointer=memory
)


def rag_agent(question: str, thread_id: str = "default"):
    logger.info(f"rag_agent called | question={question} | thread_id={thread_id}")

    result = agent.invoke(
        {"messages": [("user", question)]},
        config={"configurable": {"thread_id": thread_id}}
    )

    response = result["messages"][-1].content
    logger.info(f"rag_agent done | response={response[:80]}")
    return response