# app/agents/query_understanding_agent/prompts.py
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate

# Build the big human template using jinja2 (so braces won't break)
human_template = HumanMessagePromptTemplate.from_template(
    """
You are given the user query:
<query>
{{ User_Query }}
</query>

Conversation history:
{{ Conversation_History }}

User preferences:
{{ Preferences }}

Timestamp:
{{ Timestamp }}

Return the final output ONLY in the following JSON structure:
<schema>
{
    "intent": "qa | explain | summarize | compare | exam | debug | none",
    "rewritten_query": "string",
    "retrievers_to_use": ["vector", "keyword", "web", "youtube"],
    "retrieval_params": {
        "top_k_vector": number,
        "top_k_keyword": number,
        "top_k_web": number,
        "top_k_youtube": number
    },
    "style_preferences": {
        "type": "concise | detailed | simple | exam",
        "tone": "neutral | friendly | technical"
    }
}
</schema>

Example 1:
Input: "bro explain transformers in shortcut"
Output:
{
  "intent": "explain",
  "rewritten_query": "Explain the transformer architecture in simple terms.",
  "retrievers_to_use": ["vector", "keyword"],
  "retrieval_params": {
    "top_k_vector": 6,
    "top_k_keyword": 4,
    "top_k_web": 0,
    "top_k_youtube": 0
  },
  "style_preferences": {
    "type": "simple",
    "tone": "friendly"
  }
}

Example 2:
Input: "give expected exam questions on CNN"
Output:
{
  "intent": "exam",
  "rewritten_query": "Generate expected exam questions related to convolutional neural networks.",
  "retrievers_to_use": ["vector", "keyword"],
  "retrieval_params": {
    "top_k_vector": 5,
    "top_k_keyword": 10,
    "top_k_web": 0,
    "top_k_youtube": 0
  },
  "style_preferences": {
    "type": "exam",
    "tone": "neutral"
  }
}

Example 3:
Input: "latest research in LLMs context management"
Output:
{
  "intent": "summarize",
  "rewritten_query": "Summarize the latest research developments in large language model context management.",
  "retrievers_to_use": ["vector", "keyword", "web"],
  "retrieval_params": {
    "top_k_vector": 5,
    "top_k_keyword": 5,
    "top_k_web": 10,
    "top_k_youtube": 0
  },
  "style_preferences": {
    "type": "detailed",
    "tone": "technical"
  }
}

Example 4:
Input: "summarize this youtube video: <url>"
Output:
{
  "intent": "summarize",
  "rewritten_query": "Summarize the content of the provided YouTube video.",
  "retrievers_to_use": ["youtube"],
  "retrieval_params": {
    "top_k_vector": 0,
    "top_k_keyword": 0,
    "top_k_web": 0,
    "top_k_youtube": 1
  },
  "style_preferences": {
    "type": "concise",
    "tone": "neutral"
  }
}

Return ONLY the JSON. Nothing else.

""",
    template_format="jinja2",
)

prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are the Query Understanding Agent. Follow all instructions carefully."
        ),
        (
            "system",
            "Rewrite query, detect intent, select retrievers, set params, infer style. Output VALID JSON ONLY."
        ),
        human_template,
    ],
    template_format="jinja2",
)

# rendered = prompt_template.format(
#     User_Query="What is CNN",
#     Conversation_History=[],
#     Preferences={},
#     Timestamp="2025-11-29T12:00:00Z"
# )
# print(rendered)