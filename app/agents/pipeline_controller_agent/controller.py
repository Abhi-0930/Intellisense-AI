# app/agents/pipeline_controller_agent/controller.py
from query_understanding_agent.agent import QueryUnderstandingAgent
from retrieval_agent.orchestrator import RetrievalOrchestratorAgent
from response_synthesizer_agent.synthesizer import ResponseSynthesizer

from query_understanding_agent.schema import QueryUnderstandingInput, QueryUnderstandingOutput
from retrieval_agent.schema import RetrievalInput, RetrievalOutput
from response_synthesizer_agent.schema import SynthesisInput, SynthesisOutput

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
        tracd: Dict[str, Any] = {}
        
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
            
        
        
        # RetrievalInput Agent
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
        
        
        # Synthesizer Agent
        self.response_synthesizer_agent_input = SynthesisInput(
            trace_id = self.retrieval_agent_output.trace_id,
            user_id = user_id,
            session_id= session_id,
            query = self.query_understanding_output.rewritten_query,
            conversation_history=conversation_history,
            preferences=preferences,
            model_name=model_name,
            max_output_tokens=preferences.get("max_tokens", 400),
            retrieved_chunks=self.response_synthesizer_agent_output.chunks
        )
        
        self.response_synthesizer_agent_output: SynthesisOutput = await self.response_synthesize.run(self.response_synthesizer_agent_input)
        
        return self.response_synthesizer_agent_output # This is the final output