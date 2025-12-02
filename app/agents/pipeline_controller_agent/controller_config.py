# app/agents/pipeline_controller_agent/controller_config.py
"""
Centralized configuration for PipelineControllerAgent

All default values for 
-retriever
-model names
-max tokens
-fallback behaviours
-tracing and logging
are defined here
"""

from typing import List, Dict

DEFAULT_RETRIEVERS: List[str] = [
    "vector",
    "keyword",
]

DEFAULT_MODEL_NAME: str = "llama-3.1-8b-instant"

DEFAULT_MAX_OUTPUT_TOKENS: int = 400

FALLBACK_INSUFFICIENT_CONTEXT: str = (
    "I don't have enough information to answer that question right now. "
    "Try giving more context or allow external retrieval."
)

FALLBACK_SYNTHESIZER_FAILURE: str = (
    "Sorry, I couldn't generate a response right now. Please try again."
)

FALLBACK_QUERY_UNDERSTANDING_FAILURE: str = (
    "I'm having trouble understanding your question. "
    "Try rephrasing or providing more details."
)

ENABLE_DEBUG_LOGS: bool = True
TRACE_INCLUDE_PROMPT_HASH: bool = True
TRACE_INCLUDE_MODEL_OUTPUT_HASH: bool = True

MAX_HISTORY_TURNS: int = 12     # trim conversation history for performance
MAX_TOTAL_HISTORY_TOKENS: int = 3000