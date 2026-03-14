from pathlib import Path

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from rank_bm25 import BM25Okapi

from core.config import OPENAI_API_KEY, OPENAI_BASE_URL, EMBEDDING_MODEL

BASE_DIR = Path(__file__).resolve().parent.parent
VECTOR_DIR = BASE_DIR / "vectorstore"


class HybridRetriever:

    def __init__(self):

        self.embeddings = OpenAIEmbeddings(
            model=EMBEDDING_MODEL,
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL
        )

        self.db = FAISS.load_local(
            str(VECTOR_DIR),
            self.embeddings,
            allow_dangerous_deserialization=True
        )

        # 构建 BM25 corpus
        docs = self.db.similarity_search("", k=1000)

        self.documents = docs

        corpus = [d.page_content.split() for d in docs]

        self.bm25 = BM25Okapi(corpus)

    def retrieve(self, query, k=4):

        # BM25
        tokenized_query = query.split()

        bm25_scores = self.bm25.get_scores(tokenized_query)

        bm25_top = sorted(
            range(len(bm25_scores)),
            key=lambda i: bm25_scores[i],
            reverse=True
        )[:k]

        bm25_docs = [self.documents[i] for i in bm25_top]

        # Vector search
        vector_docs = self.db.similarity_search(query, k=k)

        # merge
        results = {d.page_content: d for d in bm25_docs}

        for d in vector_docs:
            results[d.page_content] = d

        return list(results.values())[:k]