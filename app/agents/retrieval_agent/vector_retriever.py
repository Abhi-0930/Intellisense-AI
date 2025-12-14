# app/agents/retrieval_agent/vector_retriever.py
from typing import List
from .schema import Chunk
from .utils import namespace
import asyncio
from app.core.logging import log_error, log_warning, log_info

class VectorRetriever:
    def __init__(self, vector_db_client):
        self.vector_db_client = vector_db_client
    
    async def search(self, query: str, top_k: int) -> List[Chunk]:
        try:
            log_info(f"Vector search: query='{query}', top_k={top_k}")
            results = await asyncio.to_thread(
                self.vector_db_client.search,
                namespace=namespace,
                query={
                    "top_k": top_k, 
                    "inputs": {
                        "text": query
                        }
                    }
            )

            chunk_list = []
            hits = results.get('result', {}).get('hits', [])
            
            if not hits:
                log_warning(f"Vector search returned no results for query: '{query}'")
                return []
            
            for hit in hits:
                chunk_text = hit.get('fields', {}).get("text")
                if not chunk_text:
                    log_warning(f"Hit missing 'text' field: {hit.get('_id', 'unknown')}")
                    continue
                chunk = Chunk(
                    chunk_id= hit.get('_id', ''),
                    document_id=hit.get('fields', {}).get('doc_id', ''),
                    source_type= hit.get('fields', {}).get('source_type', 'note'),
                    raw_score=hit.get('_score', 0.0),
                    text = chunk_text,
                    metadata = hit.get('fields', {}).get("category"),
                    source_url = hit.get('fields', {}).get('source_url')
                )
                chunk_list.append(chunk)
                
            chunk_list.sort(key=lambda x: x.raw_score, reverse=True)
            log_info(f"Vector search returned {len(chunk_list)} chunks")
            
            return chunk_list
        except Exception as e:
            log_error(f"Vector search failed: {str(e)}", trace_id=None)
            return []