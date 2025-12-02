# app/agents/pipeline_controller_agent/controller.py
from query_understanding_agent.agent import QueryUnderstandingAgent
from retrieval_agent.orchestrator import RetrievalOrchestratorAgent
from response_synthesizer_agent.synthesizer import ResponseSynthesizer

from query_understanding_agent.schema import QueryUnderstandingInput, QueryUnderstandingOutput
from retrieval_agent.schema import RetrievalInput, RetrievalOutput
from response_synthesizer_agent.schema import SynthesisInput, SynthesisOutput

from .controller_config import (
    DEFAULT_RETRIEVERS,
    DEFAULT_MODEL_NAME,
    DEFAULT_MAX_OUTPUT_TOKENS
)


import time
import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

class PipelineControllerAgent:
    def __init__(self, query_understander: QueryUnderstandingAgent, 
                retriever_orchestrator: RetrievalOrchestratorAgent, 
                response_synthesizer: ResponseSynthesizer
    ):
        load_dotenv()
        self.query_understander = query_understander
        self.retriever_orchestrator = retriever_orchestrator
        self.response_synthesize = response_synthesizer
        
        self.default_retrievers = DEFAULT_RETRIEVERS
        self.default_model = DEFAULT_MODEL_NAME
        self.default_max_tokens = DEFAULT_MAX_OUTPUT_TOKENS
        
    async def run(self, 
                  query: str,
                  user_id: str,
                  session_id: str,
                  preferences: Dict,
                  conversation_history: List,
                  allow_agentic: bool = False,
                  model_name: str = "llama-3.1-8b-instant"
    ) -> Dict[str, Any]:
        start_time = time.time()
        warnings: List[str] =  []
        trace: Dict[str, Any] = {}
        
        model_name = model_name or preferences.get("model_name") or self.default_model
        
        # Query Understanding Agent 
        try:
            self.query_understanding_input = QueryUnderstandingInput(
                query = query,
                user_id= user_id,
                session_id=session_id,
                preferences=preferences,
                conversation_history=conversation_history,
                timestamp=datetime.datetime.now()
            )
            self.query_understanding_output: QueryUnderstandingOutput = await self.query_understander.run(self.query_understanding_input)
        except Exception as e:
            # fallback to safe defaults
            warnings.append(f"QueryUnderstanding failed: {e}")
            self.query_understanding_output = QueryUnderstandingOutput(
                intent="unknown",
                rewritten_query=query,
                retrievers_to_use=self.default_retrievers,
                retrieval_params={},
                style_preferences={}
            )
            
            trace["query_understanding"] = {
            "rewritten_query": getattr(self.query_understanding_output, "rewritten_query", query),
            "intent": getattr(self.query_understanding_output, "intent", "unknown"),
            "retrievers_to_use": getattr(self.query_understanding_output, "retrievers_to_use", self.default_retrievers),
        }
        
        
        # RetrievalInput Agent
        try:
            self.retrieval_agent_input = RetrievalInput(
                user_id = user_id,
                session_id= session_id,
                rewritten_query= self.query_understanding_output.rewritten_query,
                retrievers_to_use= self.query_understanding_output.retrievers_to_use,
                retrieval_params= self.query_understanding_output.retrieval_params,
                conversation_history=conversation_history,
                preferences=preferences
            )
            
            self.retrieval_agent_output: RetrievalOutput = await self.retriever_orchestrator.run(self.retrieval_agent_input)
        except Exception as e:
            warnings.append(f"Retrieval failed: {e}")
            # Fallback: empty retrieval output structure
            retrieval_output = RetrievalOutput(
                chunks=[],
                retrieval_trace={},
                trace_id=f"fallback-{int(time.time() * 1000)}",
            )
        trace["retrieval_trace"] = getattr(retrieval_output, "retrieval_trace", {})
        
        # Synthesizer Agent
        try:
            self.response_synthesizer_agent_input = SynthesisInput(
                trace_id = self.retrieval_agent_output.trace_id,
                user_id = user_id,
                session_id= session_id,
                query = self.query_understanding_output.rewritten_query,
                conversation_history=conversation_history,
                preferences=preferences,
                model_name=model_name,
                max_output_tokens=preferences.get("max_tokens", self.default_max_tokens),
                retrieved_chunks=self.response_synthesizer_agent_output.chunks
            )
            
            self.response_synthesizer_agent_output: SynthesisOutput = await self.response_synthesize.run(self.response_synthesizer_agent_input)
        except Exception as e:
            warnings.append(f"Synthesizer failed: {e}")
            synthesis_output = SynthesisOutput(
                answer="Sorry, I couldn't generate a response right now.",
                citations=[],
                warnings=[str(e)],
                confidence=0.0,
                raw_model_output=None,
                used_chunk_ids=[],
                reasoning=None,
                metrics={},
            )

        # Handle INSFFICIENT_CONTEXT sentinel if your synthesizer uses that
        if getattr(synthesis_output, "answer", None) == "INSUFFICIENT_CONTEXT":
            warnings.append("Synthesizer reported INSUFFICIENT_CONTEXT. Returning fallback answer.")
            fallback_answer = "I don't have enough information to answer that question right now. " \
                              "Try giving more context or allow retrieval of external sources."
            synthesis_output.answer = fallback_answer
            synthesis_output.confidence = 0.0


        latency_ms = int((time.time() - start_time) * 1000)

        final_payload = {
            "answer": synthesis_output.answer,
            "confidence": getattr(synthesis_output, "confidence", 0.0),
            "warnings": warnings + getattr(synthesis_output, "warnings", []),
            "citations": getattr(synthesis_output, "citations", []),
            "used_chunk_ids": getattr(synthesis_output, "used_chunk_ids", getattr(synthesis_output, "used_chunk_ids", [])),
            "retrieval_trace": trace.get("retrieval_trace", {}),
            "query_understanding": trace.get("query_understanding", {}),
            "trace_id": getattr(retrieval_output, "trace_id", None),
            "latency_ms": latency_ms,
            "raw_model_output": getattr(synthesis_output, "raw_model_output", None),
            "metrics": getattr(synthesis_output, "metrics", {}),
        }

        return final_payload # final output