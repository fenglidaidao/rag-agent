# agents/general_agent.py
from langgraph.prebuilt import create_react_agent
from core.llm import get_llm
from memory.memory import memory
from core.logger import get_logger

logger = get_logger("general_agent")

llm = get_llm()

# ✅ 和 tool_agent 一样，用 create_react_agent + memory
agent = create_react_agent(
    llm,
    tools=[],          # general agent 不需要工具
    checkpointer=memory
)


def general_agent(question: str, thread_id: str = "default"):
    logger.info(f"general_agent | thread_id={thread_id} | question={question}")

    result = agent.invoke(
        {"messages": [("user", question)]},
        config={"configurable": {"thread_id": thread_id}}
    )

    # 打印当前完整消息历史，确认 memory 是否在积累
    all_messages = result["messages"]
    logger.info(f"general_agent | 消息历史长度={len(all_messages)}")
    for i, msg in enumerate(all_messages):
        logger.info(f"  [{i}] {msg.type}: {str(msg.content)[:60]}")

    return all_messages[-1].content