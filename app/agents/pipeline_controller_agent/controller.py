# app/agents/pipeline_controller_agent/controller.py
from app.agents.query_understanding_agent.agent import QueryUnderstandingAgent
from app.agents.retrieval_agent.orchestrator import RetrievalOrchestratorAgent
from app.agents.response_synthesizer_agent.synthesizer import ResponseSynthesizer

from app.agents.query_understanding_agent.schema import (
    QueryUnderstandingInput,
    QueryUnderstandingOutput,
    Preferences
)

# IMPORTANT FIX: Import RetrievalParams from retrieval agent schema
from app.agents.retrieval_agent.schema import (
    RetrievalInput,
    RetrievalOutput,
    RetrievalParams as RetrievalParams_RetrievalAgent,
)

from app.agents.response_synthesizer_agent.schema import SynthesisInput, SynthesisOutput

from .controller_config import (
    DEFAULT_RETRIEVERS,
    DEFAULT_MODEL_NAME,
    DEFAULT_MAX_OUTPUT_TOKENS,
    FALLBACK_INSUFFICIENT_CONTEXT,
    FALLBACK_QUERY_UNDERSTANDING_FAILURE,
    FALLBACK_SYNTHESIZER_FAILURE
)

import time
import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv


class PipelineControllerAgent:
    def __init__(
        self,
        query_understander: QueryUnderstandingAgent,
        retriever_orchestrator: RetrievalOrchestratorAgent,
        response_synthesizer: ResponseSynthesizer
    ):
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
        self.query_understander = query_understander
        self.retriever_orchestrator = retriever_orchestrator
        self.response_synthesizer = response_synthesizer

        self.default_retrievers = DEFAULT_RETRIEVERS
        self.default_model = DEFAULT_MODEL_NAME
        self.default_max_tokens = DEFAULT_MAX_OUTPUT_TOKENS

    async def run(
        self,
        query: str,
        user_id: str,
        session_id: str,
        preferences: Preferences,
        conversation_history: List,
        allow_agentic: bool = False,
        model_name: str = "llama-3.1-8b-instant"
    ) -> Dict[str, Any]:

        start_time = time.time()
        warnings: List[str] = []
        trace: Dict[str, Any] = {}

        # Model selection
        model_name = model_name or self.default_model

        prefs = Preferences(
            response_style=preferences.get("response_style", "concise"),
            max_length=preferences.get("max_length", 300),
            domain=preferences.get("domain", "general")
        )

        # ======================
        # 1. QUERY UNDERSTANDING
        # ======================
        try:
            self.query_understanding_input = QueryUnderstandingInput(
                query_text=query,
                user_id=user_id,
                session_id=session_id,
                preferences=prefs,
                conversation_history=conversation_history,
                timestamp=datetime.datetime.now()
            )
            self.query_understanding_output: QueryUnderstandingOutput = \
                await self.query_understander.run(self.query_understanding_input)

            trace["query_understanding"] = {
                "rewritten_query": self.query_understanding_output.rewritten_query,
                "intent": self.query_understanding_output.intent,
                "retrievers_to_use": self.query_understanding_output.retrievers_to_use,
                "retrieval_params": self.query_understanding_output.retrieval_params.model_dump(),
                "style_preferences": self.query_understanding_output.style_preferences.model_dump(),
            }

        except Exception as e:
            from app.agents.query_understanding_agent.schema import RetrievalParams, StylePreferences

            warnings.append(f"QueryUnderstanding failed: {e}")

            default_retrieval_params = RetrievalParams(
                top_k_vector=6,
                top_k_keyword=4,
                top_k_web=3,
                top_k_youtube=1
            )
            default_style = StylePreferences(
                type="concise",
                tone="neutral"
            )

            self.query_understanding_output = QueryUnderstandingOutput(
                intent="none",
                rewritten_query=query,
                retrievers_to_use=self.default_retrievers,
                retrieval_params=default_retrieval_params,
                style_preferences=default_style
            )

            trace["query_understanding"] = {
                "rewritten_query": query,
                "intent": "none",
                "retrievers_to_use": self.default_retrievers,
                "retrieval_params": default_retrieval_params.model_dump(),
                "style_preferences": default_style.model_dump(),
            }

        # ======================
        # 2. RETRIEVAL
        # ======================
        try:
            # 🔥 CRITICAL FIX: convert QueryUnderstanding RetrievalParams → RetrievalAgent RetrievalParams
            converted_params = RetrievalParams_RetrievalAgent(
                **self.query_understanding_output.retrieval_params.model_dump()
            )

            self.retrieval_agent_input = RetrievalInput(
                user_id=user_id,
                session_id=session_id,
                rewritten_query=self.query_understanding_output.rewritten_query,
                retrievers_to_use=self.query_understanding_output.retrievers_to_use,
                retrieval_params=converted_params,     # ← FIX
                conversation_history=conversation_history,
                preferences=preferences
            )

            self.retrieval_agent_output: RetrievalOutput = \
                await self.retriever_orchestrator.run(self.retrieval_agent_input)

        except Exception as e:
            warnings.append(f"Retrieval failed: {e}")
            self.retrieval_agent_output = RetrievalOutput(
                chunks=[],
                retrieval_trace={},
                trace_id=f"fallback-{int(time.time() * 1000)}",
            )

        trace["retrieval_trace"] = self.retrieval_agent_output.retrieval_trace

        # ======================
        # 3. SYNTHESIS
        # ======================
        try:
            self.response_synthesizer_agent_input = SynthesisInput(
                trace_id=self.retrieval_agent_output.trace_id,
                user_id=user_id,
                session_id=session_id,
                query=self.query_understanding_output.rewritten_query,
                conversation_history=conversation_history,
                preferences=preferences,
                model_name=model_name,
                max_output_tokens=preferences.get("max_tokens", self.default_max_tokens),
                retrieved_chunks=self.retrieval_agent_output.chunks
            )
            self.response_synthesizer_agent_output: SynthesisOutput = \
                await self.response_synthesizer.run(self.response_synthesizer_agent_input)

        except Exception as e:
            warnings.append(f"Synthesizer failed: {e}")
            self.response_synthesizer_agent_output = SynthesisOutput(
                answer=FALLBACK_SYNTHESIZER_FAILURE,
                used_chunk_ids=[],
                trace_id=self.retrieval_agent_output.trace_id,
                confidence=0.0,
                warnings=[str(e)],
                raw_model_output=None,
                reasoning=None,
                metrics={},
            )

        if self.response_synthesizer_agent_output.answer == "INSUFFICIENT_CONTEXT":
            warnings.append("Synthesizer reported INSUFFICIENT_CONTEXT.")
            self.response_synthesizer_agent_output.answer = FALLBACK_INSUFFICIENT_CONTEXT
            self.response_synthesizer_agent_output.confidence = 0.0

        # ======================
        # FINAL OUTPUT
        # ======================
        latency_ms = int((time.time() - start_time) * 1000)

        final_payload = {
            "answer": self.response_synthesizer_agent_output.answer,
            "confidence": self.response_synthesizer_agent_output.confidence,
            "warnings": warnings + self.response_synthesizer_agent_output.warnings,
            "used_chunk_ids": self.response_synthesizer_agent_output.used_chunk_ids,
            "retrieval_trace": trace["retrieval_trace"],
            "query_understanding": trace["query_understanding"],
            "trace_id": self.response_synthesizer_agent_output.trace_id,
            "latency_ms": latency_ms,
            "raw_model_output": self.response_synthesizer_agent_output.raw_model_output,
            "metrics": self.response_synthesizer_agent_output.metrics,
        }

        return final_payload
