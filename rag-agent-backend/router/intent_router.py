from core.llm import get_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from core.logger import get_logger
logger = get_logger("intent_router")

llm = get_llm()

router_prompt = ChatPromptTemplate.from_template(
"""
你是一个意图分类器，请判断用户问题属于哪个类别。

只返回以下标签之一，不要有任何其他内容：

rag     -> 需要查询内部知识库、文档、文件内容、图片内容相关的问题
tool    -> 需要调用外部工具的问题，例如：天气、时间、计算、搜索
chat    -> 普通闲聊或通用问题

示例：
"docker有哪些命令" -> rag
"这张图片里有什么" -> rag
"图片中的内容是什么" -> rag
"文件里说了什么" -> rag
"上传的图片描述一下" -> rag
"上海今天天气怎么样" -> tool
"帮我查一下北京的天气" -> tool
"你好" -> chat
"langchain是什么" -> chat

用户问题：
{question}
"""
)

chain = router_prompt | llm | StrOutputParser()


def route(question: str):
    intent = chain.invoke({"question": question}).strip().lower()
    logger.info(f"ROUTER:{intent}")
    return intent