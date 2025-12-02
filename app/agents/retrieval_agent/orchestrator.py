# app/agents/retrieval_agent/orchestrator.py

from app.agents.retrieval_agent.schema import Chunk, RetrievalInput, RetrievalOutput, RetrievalParams
from app.agents.retrieval_agent.vector_retriever import VectorRetriever
from app.agents.retrieval_agent.keyword_retriever import KeywordRetriever
from typing import List
from uuid import uuid4
class RetrievalOrchestratorAgent:
    def __init__(self, vector_retriever: VectorRetriever, keyword_retriever: KeywordRetriever):
        self.vector_retriever = vector_retriever
        self.keyword_retriever = keyword_retriever
        
        print(f"Vector retriever: {vector_retriever}") 
        print(f"Keyword retriever: {keyword_retriever}") 
        
    def create_trace(self):
        return uuid4() # it returns the trace_id for RetrievalOutput
        
    async def run(self, input: RetrievalInput) -> RetrievalOutput:
        
        self.vector_chunks = []
        self.keyword_chunks = []
        
        self.trace_id = self.create_trace()
        self.retrieval_trace = {
            "trace_id": self.trace_id,
            "query": input.rewritten_query,
            "retrievers_used": input.retrievers_to_use,
            "results": {
                "vector": None,
                "keyword": None
            }
        }
        
        if "vector" in input.retrievers_to_use:
            self.vector_chunks = await self.vector_retriever.search(
                query = input.rewritten_query, 
                top_k = input.retrieval_params.top_k_vector
            )
            self.retrieval_trace['results']['vector'] = {
                "count": len(self.vector_chunks),
                "top_k": input.retrieval_params.top_k_vector,
                "status": "success"
            }
            
        if "keyword" in input.retrievers_to_use: 
            self.keyword_chunks = await self.keyword_retriever.search(
                query = input.rewritten_query,
                top_k = input.retrieval_params.top_k_keyword
            )
            
            self.retrieval_trace['results']['keyword'] = {
                "count": len(self.keyword_chunks),
                "top_k": input.retrieval_params.top_k_keyword,
                "status": "success"
            }
            
        merged = self.merge_chunks([self.keyword_chunks, self.vector_chunks])
        final_chunks = self.normalize_scores(merged)
        
        final_chunks.sort(key=lambda c: c.normalized_score, reverse=True)
        
        retrieval_output = RetrievalOutput(
            chunks = final_chunks,
            retrieval_trace = self.retrieval_trace,
            trace_id = self.trace_id
        )
        
        return retrieval_output
        
    def normalize_scores(self, chunks: List[Chunk]):
        if not chunks:
            return []
        
        max_score = max(chunk.raw_score for chunk in chunks)
        max_score = max(max_score, 1e-8)
        for chunk in chunks:
            chunk.normalized_score = chunk.raw_score/max_score
        
        return chunks
    
    def merge_chunks(self, all_chunks_list):
        
        flat = []
        for lst in all_chunks_list:
            if lst:
                flat.extend(lst)

        if not flat:
            return []

        unique = {}

        for chunk in flat:
            # Determine-key for deduplication
            # Priority: chunk_id → fallback: hash(text)
            key = chunk.chunk_id or f"text_hash_{hash(chunk.text)}"

            if key not in unique:
                # First time seeing this chunk
                unique[key] = chunk
            else:
                # Already exists → keep one with HIGHER raw_score
                if chunk.raw_score > unique[key].raw_score:
                    unique[key] = chunk

        return list(unique.values())