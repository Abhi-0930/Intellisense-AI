# app/agents/retrieval_agent/vector_retriever.py
from typing import List
from .schema import Chunk
from .utils import namespace
import asyncio
class VectorRetriever:
    def __init__(self, vector_db_client):
        self.vector_db_client = vector_db_client
    
    async def search(self, query: str, top_k: int) -> List[Chunk]:
        try:
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
            for hit in results['result']['hits']:
                chunk_text = hit['fields'].get("text")
                if not chunk_text:
                    continue
                chunk = Chunk(
                    chunk_id= hit['_id'],
                    document_id=hit['fields'].get('doc_id', ''),
                    source_type= hit['fields'].get('source_type', 'note'),
                    raw_score=hit['_score'],
                    text = chunk_text,
                    metadata = hit["fields"].get("category"),
                    source_url = hit['fields'].get('source_url')
                )
                chunk_list.append(chunk)
                
            chunk_list.sort(key=lambda x: x.raw_score, reverse=True)
            
            return chunk_list
        except Exception as e:
            return []