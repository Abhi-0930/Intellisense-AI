# app/agents/query_understanding_agent/agent.py
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from app.agents.query_understanding_agent.schema import QueryUnderstandingInput, QueryUnderstandingOutput
from app.agents.query_understanding_agent.prompts import prompt_template
import json

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
            "query_text": "what are vision transformers and explain in exam pov",
            "conversation_history": [],
            "preferences": {
                "response_style": "detailed",
                "max_length": 500,
                "domain": "artificial intelligene" 
                },
            "timestamp": datetime.now()
        }
        test_model = QueryUnderstandingInput(**my_prompt)
        response = await ob.run(test_model)
        print(response)
        
    asyncio.run(main())