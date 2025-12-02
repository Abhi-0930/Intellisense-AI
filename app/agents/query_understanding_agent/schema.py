# app/agents/query_understanding_agent/schema.py
from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

class Preferences(BaseModel):
    response_style: str
    max_length: int
    domain: str

class QueryUnderstandingInput(BaseModel):
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    query_text: str
    conversation_history: List[str] = Field(..., max_items=3)
    preferences: Preferences
    timestamp: Optional[datetime] = None
    
class RetrievalParams(BaseModel):
    top_k_vector: int
    top_k_keyword: int
    top_k_web: int
    top_k_youtube: int
    
class StylePreferences(BaseModel):
    type: Literal["concise", "detailed", "simple", "exam"]
    tone: Literal["neutral", "friendly", "technical"]

class QueryUnderstandingOutput(BaseModel):
    intent: Literal["qa", "explain", "summarize", "compare", "exam", "debug", "none"]
    rewritten_query: str
    retrievers_to_use: List[Literal["vector", "keyword", "web", "youtube"]] = Field(..., min_items = 1)
    retrieval_params: RetrievalParams
    style_preferences: StylePreferences
    