# app/agents/query_understanding_agent/agent.py
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from schema import QueryUnderstandingInput, QueryUnderstandingOutput
from prompts import prompt_template
import json
load_dotenv()
class QueryUnderstandingAgent:
    def __init__(self, llm_client):
        self.llm_client = llm_client

    def build_prompt(self, input: QueryUnderstandingInput):
        """
        Prepares variables for the prompt template
        """
        prompt = prompt_template.format(
            User_Query = input.query_text,
            Conversation_History = input.conversation_history,
            Preferences = input.preferences.model_dump(),
            Timestamp = input.timestamp.isoformat()
        )
        
        return prompt
        
        
    async def run(self, input: QueryUnderstandingInput) -> QueryUnderstandingOutput:
        """
        Main entry point for this agent
        """
        prompt = self.build_prompt(input=input)
        response = await self.llm_client.ainvoke(prompt)
        raw_output = response.content
        parsed = json.loads(raw_output)
        return QueryUnderstandingOutput(**parsed)

from datetime import datetime
import asyncio

if __name__ == "__main__":
    async def main():
        ob = QueryUnderstandingAgent(ChatGroq(model="llama-3.1-8b-instant"))
        my_prompt = {
            "query_text": "Explain CNN in simple terms",
            "conversation_history": [],
            "preferences": {
                "response_style": "detailed",
                "max_length": 500,
                "domain": "deep learning" 
                },
            "timestamp": datetime.now()
        }
        test_model = QueryUnderstandingInput(**my_prompt)
        response = await ob.run(test_model)
        print(response)
        
    asyncio.run(main())