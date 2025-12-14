# app/api/routes/chat_router.py
from fastapi import APIRouter, Depends, HTTPException, Request, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.redis_client import redis_client

from app.agents.pipeline_controller_agent.controller import PipelineControllerAgent
from app.agents.query_understanding_agent.agent import QueryUnderstandingAgent

from app.agents.response_synthesizer_agent.synthesizer import ResponseSynthesizer
from app.agents.response_synthesizer_agent.utils import estimate_tokens
from app.agents.response_synthesizer_agent.prompts import SYSTEM_PROMPT, INSTRUCTION_PROMPT
from app.agents.response_synthesizer_agent.model_config import ModelConfig

from app.agents.retrieval_agent.orchestrator import RetrievalOrchestratorAgent
from app.agents.retrieval_agent.keyword_retriever import KeywordRetriever
from app.agents.retrieval_agent.vector_retriever import VectorRetriever
from app.agents.retrieval_agent.utils import index

from app.api.schemas.chat_request import ChatRequest
from app.api.schemas.chat_response import ChatResponse

from app.core.auth_utils import decode_jwt_token

from dotenv import load_dotenv

from langchain_groq import ChatGroq

import time
bearer_scheme = HTTPBearer()
def ensure_valid_session(user_id: str, session_id: str):
    key = f"session:{session_id}"
    
    # session does not exists -> expired or wrong ID
    if not redis_client.exists(key):
        raise HTTPException(400, "Session not found or expired")
    
    stored_user_id = redis_client.hget(key, "user_id")
    
    # someone might pass a session belonging to another user
    if stored_user_id != user_id:
        raise HTTPException(400, "Session does not belong to this user")

router = APIRouter(prefix="/v1/chat",
                   tags=["chat (Notebook LM)"]
                   )

pipeline_controller: PipelineControllerAgent = None

def get_pipeline_controller() -> PipelineControllerAgent:
    global pipeline_controller

    if pipeline_controller is None:
        # Load .env file with encoding fallback
        try:
            load_dotenv()
        except UnicodeDecodeError:
            # Try UTF-16 encoding (common on Windows)
            try:
                load_dotenv(encoding='utf-16')
            except Exception:
                # Try UTF-16 with BOM
                try:
                    load_dotenv(encoding='utf-16-le')
                except Exception:
                    # If all encodings fail, continue without .env file
                    pass

        vector_client = VectorRetriever(index)
        keyword_client = KeywordRetriever("app/agents/retrieval_agent/keyword_index.json")
        llm_client = ChatGroq(model="llama-3.1-8b-instant")

        q_agent = QueryUnderstandingAgent(llm_client)
        retrieval_agent = RetrievalOrchestratorAgent(
            vector_retriever=vector_client,
            keyword_retriever=keyword_client
        )
        model_config = ModelConfig(
            model_name="llama-3.1-8b-instant",
            max_context_tokens=128000      # adjust to model's limit
        )

        prompts = {
            "system": SYSTEM_PROMPT,
            "instruction": INSTRUCTION_PROMPT
        }

        res_agent = ResponseSynthesizer(
            llm_client=llm_client,
            token_estimator=estimate_tokens,
            prompts=prompts,
            model_config=model_config
        )

        pipeline_controller = PipelineControllerAgent(
            q_agent,
            retrieval_agent,
            res_agent
        )

    return pipeline_controller

@router.post("/query")
async def chat_query(
                     http_request: Request,
                     request: ChatRequest, 
                     credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
                     controller: PipelineControllerAgent = Depends(get_pipeline_controller)
                    ) -> ChatResponse:
    try:    
        token = credentials.credentials
        decoded = decode_jwt_token(token)
        
        if not decoded:
            raise HTTPException(401, "Invalid or expired token")
        
        authenticated_user_id = decoded["user_id"]
        
        if authenticated_user_id != request.user_id:
            raise HTTPException(403, "Token does not match user")
        
        ensure_valid_session(request.user_id, request.session_id)
        response = await controller.run(
            query= request.query,
            user_id = request.user_id,
            session_id= request.session_id,
            preferences= request.preferences,
            conversation_history= request.conversation_history,
            allow_agentic=request.allow_agentic,
            model_name=request.model_name
        )
        
        return ChatResponse(
            answer = response.get("answer"),
            confidence=response.get("confidence"),
            warnings= response.get("warnings"),
            used_chunk_ids= response.get("used_chunk_ids"),
            retrieval_trace=response.get("retrieval_trace"),
            query_understanding=response.get("query_understanding"),
            trace_id=response.get("trace_id"),
            latency_ms=response.get("latency_ms"),
            raw_model_output=response.get("raw_model_output"),
            metrics=response.get("metrics"),
            citations = []
        )
        
    except Exception as e:
        from app.core.logging import log_error
        import traceback
        
        # Log the full error with traceback
        error_trace = traceback.format_exc()
        trace_id = http_request.headers.get("X-Trace-ID", "none")
        log_error(f"Chat query failed: {str(e)}\n{error_trace}", trace_id=trace_id)
        
        fallback_answer = (
            "Sorry, something went wrong while processing your request. "
            "Please try again."
        )

        return ChatResponse(
            answer=fallback_answer,
            confidence=0.0,
            warnings=["controller_failed", str(e)],
            used_chunk_ids=[],
            retrieval_trace={},
            query_understanding={},
            trace_id=f"fallback-{int(time.time()*1000)}",
            latency_ms=0,
            raw_model_output=None,
            metrics={},
            citations=[]
        )