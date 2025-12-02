# app/agents/response_synthesizer_agent/model_config.py
class ModelConfig:
    def __init__(self, model_name: str, max_context_tokens: int):
        self.model_name = model_name
        self.max_context_tokens = max_context_tokens
