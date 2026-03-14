# rag/rag_chain.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from core.llm import get_llm

llm = get_llm()

prompt = ChatPromptTemplate.from_template("""
Answer the question based only on the context.

Context:
{context}

Question:
{question}
""")

parser = StrOutputParser()

def run_rag(question: str):
    # ✅ 延迟初始化，避免启动时 vectorstore 不存在报错
    from rag.retriever import HybridRetriever
    retriever = HybridRetriever()

    docs = retriever.retrieve(question)
    context = "\n\n".join([d.page_content for d in docs])
    chain = prompt | llm | parser
    return chain.invoke({"context": context, "question": question})
