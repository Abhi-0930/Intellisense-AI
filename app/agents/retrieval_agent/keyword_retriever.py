# app/agents/retrieval_agent/keyword_retriever.py

from typing import List
from app.agents.retrieval_agent.schema import Chunk
import json
import os
import re
import math
from rank_bm25 import BM25Okapi


def tokenize(text: str) -> List[str]:
    """
    Regex tokenizer: removes punctuation, lowercases,
    and splits on word boundaries.
    """
    return re.findall(r"\b\w+\b", text.lower())


class KeywordRetriever:
    def __init__(self, keyword_index_path: str = "app/agents/retrieval_agent/keyword_index.json"):
        if not os.path.exists(keyword_index_path):
            raise FileNotFoundError(f"Keyword Index not found at: {keyword_index_path}")

        with open(keyword_index_path, "r", encoding="utf-8") as f:
            self.docs = json.load(f)

        # Prepare tokenized corpus
        self.texts = [tokenize(d["text"]) for d in self.docs]
        self.bm25 = BM25Okapi(self.texts)

    async def search(self, query: str, top_k: int) -> List[Chunk]:
        query_tokens = tokenize(query)
        scores = self.bm25.get_scores(query_tokens)

        # Normalize scores for stability
        max_score = max(scores) or 1.0

        ranked = sorted(
            list(zip(scores, self.docs)),
            key=lambda x: x[0],
            reverse=True,
        )[:top_k]

        chunks = []
        for score, item in ranked:
            chunks.append(
                Chunk(
                    chunk_id=item["chunk_id"],
                    document_id=item.get("document_id", ""),
                    text=item["text"],
                    source_type=item.get("source_type", "note"),
                    source_url=item.get("source_url"),
                    metadata=item.get("metadata", {}),
                    raw_score=score,                             # actual BM25 score
                    normalized_score=score / max_score,          # normalized (0–1)
                    # log_score=math.log(1 + score)                # log score for tiny values
                )
            )
        return chunks


# Test runner (executed when run directly)
if __name__ == "__main__":
    import asyncio

    async def test():
        print("\nRunning KeywordRetriever test:\n")
        kw = KeywordRetriever("keyword_index.json")
        res = await kw.search("What is Eiffel Tower", top_k=5)

        for c in res:
            print(c)

    asyncio.run(test())
