# app/agents/retrieval_agent/schema.py
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any

class RetrievalParams(BaseModel):
    top_k_vector: int = 8
    top_k_keyword: int = 5
    top_k_web: int = 3
    top_k_youtube: int = 3


class RetrievalInput(BaseModel):
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    rewritten_query: str
    retrievers_to_use: List[
        Literal["vector", "keyword", "web", "youtube"]
    ]
    retrieval_params: RetrievalParams
    conversation_history: List[str] = []
    preferences: dict
    
class Chunk(BaseModel):
    chunk_id: Optional[str]
    document_id: str
    text: str
    source_type: Literal["pdf","web","youtube","note"]
    source_url: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    metadata: Optional[dict] = None
    raw_score: float              
    normalized_score: float = 0.0

class RetrievalOutput(BaseModel):
    chunks: List[Chunk]                
    retrieval_trace: Dict[str, Any]              
    trace_id: str