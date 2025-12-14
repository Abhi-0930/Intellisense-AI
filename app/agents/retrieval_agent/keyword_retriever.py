# app/agents/retrieval_agent/keyword_retriever.py

from typing import List
from app.agents.retrieval_agent.schema import Chunk
import json
import os
import re
import math
from rank_bm25 import BM25Okapi
from app.core.logging import log_info, log_warning


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
        log_info(f"Keyword search: query='{query}', top_k={top_k}, corpus_size={len(self.docs)}")
        query_tokens = tokenize(query)
        
        if not query_tokens:
            log_warning(f"Keyword search: query tokenized to empty list: '{query}'")
            return []
        
        scores = self.bm25.get_scores(query_tokens)

        # Normalize scores for stability
        # scores is a numpy array, convert to list to avoid ambiguity
        scores_list = scores.tolist() if hasattr(scores, 'tolist') else list(scores)
        max_score = float(max(scores_list)) if len(scores_list) > 0 and max(scores_list) > 0 else 1.0

        ranked = sorted(
            list(zip(scores_list, self.docs)),
            key=lambda x: x[0],
            reverse=True,
        )[:top_k]

        chunks = []
        for score, item in ranked:
            # Include all ranked chunks, even with low scores (they're still the best matches)
            # This ensures we always return something if the corpus has data
            chunks.append(
                Chunk(
                    chunk_id=item["chunk_id"],
                    document_id=item.get("document_id", ""),
                    text=item["text"],
                    source_type=item.get("source_type", "note"),
                    source_url=item.get("source_url"),
                    metadata=item.get("metadata", {}),
                    raw_score=score,                             # actual BM25 score
                    normalized_score=score / max_score if max_score > 0 else 0.0,          # normalized (0–1)
                    # log_score=math.log(1 + score)                # log score for tiny values
                )
            )
        
        log_info(f"Keyword search returned {len(chunks)} chunks (max_score={max_score:.4f})")
        if len(chunks) == 0:
            log_warning(f"Keyword search returned 0 chunks despite corpus having {len(self.docs)} documents")
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
