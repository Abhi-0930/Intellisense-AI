# app/agents/response_synthesizer_agent/synthesizer.py
import time
import hashlib
import re
from typing import List, Dict, Optional
from langchain_groq import ChatGroq
from .schema import SynthesisInput, SynthesisOutput
from .utils import estimate_tokens, sentence_tokenize, clean_text, token_overlap
from .prompts import SYSTEM_PROMPT, INSTRUCTION_PROMPT

class ResponseSynthesizer:
    def __init__(self, llm_client: ChatGroq, token_estimator, prompts, model_config):
        self.llm_clinet = llm_client
        self.token_estimator = token_estimator
        self.prompts = prompts
        self.model_config = model_config
    
    async def run(self, input: SynthesisInput) -> SynthesisOutput:
        
        start_time = time.time()
        
        if not input.trace_id:
            raise Exception("Trace ID does not exists!!")
        if not input.query:
            raise Exception("Query not found!")
        if input.retrieved_chunks is None:
            raise Exception("retrieved_chunks must not be None")

        # EMPTY CONTEXT FALLBACK
        if len(input.retrieved_chunks) == 0:
            fallback_answer = (
                "I don’t have any information on that in the available sources. "
                "Would you like me to search the web or provide more documents?"
            )
            return SynthesisOutput(
                answer=fallback_answer,
                used_chunk_ids=[],
                trace_id=input.trace_id,
                confidence=0.0,
                warnings=["no_retrieved_chunks"],
                raw_model_output=None,
                reasoning=None,
                metrics={"latency_ms": int((time.time() - start_time) * 1000)},
            )
            
            
        included_chunks = self.select_chunks(
            chunks = input.retrieved_chunks,
            query = input.query
        )
        
        # build context
        context_text = self.build_context(included_chunks)
        context_hash = hashlib.sha256(context_text.encode()).hexdigest()
        
        # construct the prompt
        prompt = self.build_prompt(
            query = input.query,
            preferences = input.preferences,
            context = context_text,
            history = input.conversation_history
        )
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
        
        # call llm
        raw_output, token_usage = await self.call_llm(
            prompt,
            max_tokens = input.max_output_tokens or 512,
            model_name = input.model_name or self.model_config.model_name
        )
        
        # if model say insufficient context -> fallback
        if raw_output.strip() == "INSUFFICIENT_CONTEXT":
            fallback = (
                "INSUFFICIENT_CONTEXT - I don't have enough reliable information "
                "in the provided sources to answer that confidently. " 
            )
            
            return SynthesisOutput(
                answer=fallback,
                used_chunk_ids=[],
                trace_id=input.trace_id,
                confidence=0.0,
                warnings=["insufficinet_context"],
                raw_model_output=raw_output,
                reasoning=None,
                metrics = token_usage
            )
            
        # post processing
        processed_answer, used_chunk_ids, warnings = self.postprocess(
            raw_output,
            included_chunks
        )
        
        # if postprocess detected insufficient info
        if processed_answer == "INSUFFICIENT_CONTEXT":
            insufficient_msg = (
                "INSUFFICIENT_CONTEXT - I don't have enought reliable information "
                "in the provided sources to asnwer that confidently."
            )
            
            return SynthesisOutput(
                answer=insufficient_msg,
                used_chunk_ids=[],
                trace_id=input.trace_id,
                confidence=0.0,
                warnings=warnings,
                raw_model_output=raw_output,
                reasoning=None,
                metrics=token_usage,
            )
        
        confidence = self.compute_confidence(used_chunk_ids, included_chunks, warnings)
        
        # return final output
        latency_ms = int((time.time() - start_time) * 1000)
        
        return SynthesisOutput(
            answer = processed_answer,
            used_chunk_ids=used_chunk_ids,
            trace_id=input.trace_id,
            confidence=confidence,
            warnings=warnings,
            raw_model_output=raw_output,
            reasoning=None,
            metrics = {
                "latency_ms": latency_ms,
                **token_usage
            }
        )
        
    def select_chunks(self, chunks, query) -> List:
        """
        Select chunks according to token budget.
        Excerpt chunks when necessary.
        """
        
        max_ctx = self.model_config.max_context_tokens
        reserved = 1500
        safety = 256
        available = max_ctx - reserved - safety
        
        # sort by final score
        chunks = sorted(chunks, key=lambda c:c.score, reverse=True)
        
        included = []
        used_tokens = 0
        
        for chunk in chunks:
            full_text = chunk.text 
            tok = estimate_tokens(full_text)
            
            # if fits
            if used_tokens + tok <= available:
                included.append(chunk)
                used_tokens += tok
                continue
            
            # if not fit -> excerpt top relevant sentences
            sentences = sentence_tokenize(full_text)
            scored = [(token_overlap(query, s), s) for s in sentences]
            scored.sort(reverse=True)
            
            excerpt = " ".join([s for _, s in scored[:3]])  # top 3 relevant sentences
            excerpt_tok = estimate_tokens(excerpt)

            if excerpt_tok <= available - used_tokens:
                chunk.text = excerpt
                chunk.metadata["truncated"] = True
                included.append(chunk)
                break

            # Otherwise cannot include further chunks
            break

        return included
    
    def build_context(self, chunks: List) -> str:
        blocks = []
        for i, c in enumerate(chunks):
            block = (
                f"CHUNK HEADER: [CHUNK {i}] source_type: {c.metadata.get('source_type','local')} | "
                f"source_url: {c.source_url or 'local'} | chunk_id: {c.chunk_id}\n"
                f"CHUNK BODY:\n{clean_text(c.text)}\n"
                f"METADATA: category: {c.metadata.get('category','n/a')} | "
                f"score: {c.score} | retriever: {c.metadata.get('retriever','unknown')} | "
                f"created_at: {c.metadata.get('created_at','n/a')}\n"
                f"---END CHUNK---"
            )
            blocks.append(block)

        summary = f"Context summary: {len(chunks)} chunks included; top_topics: n/a"

        return f"CONTEXT_START\n{summary}\n" + "\n---\n".join(blocks) + "\nCONTEXT_END"

    # ---------------------------------------------------------
    # PROMPT BUILDER
    # ---------------------------------------------------------
    def build_prompt(self, query, preferences, context, history):
        hist = history[-3:] if history else []
        hist_text = "\n".join(hist)

        instruction = INSTRUCTION_PROMPT.format(
            query=query,
            preferences=preferences,
            context_blocks=context,
        )

        full_prompt = (
            SYSTEM_PROMPT
            + "\n"
            + instruction
            + "\nConversation History:\n"
            + hist_text
            + "\n"
        )
        return full_prompt

    # ---------------------------------------------------------
    # LLM CALL
    # ---------------------------------------------------------
    async def call_llm(self, prompt, max_tokens, model_name):
        result = await self.llm_client.apredict(
            prompt=prompt,
            max_tokens=max_tokens,
            model=model_name,
            temperature=0.0,
        )
        # token usage from provider (if available)
        token_usage = {"tokens": len(prompt.split()) + len(result.split())}
        return result, token_usage

    # ---------------------------------------------------------
    # POSTPROCESSING / FACT CHECKING
    # ---------------------------------------------------------
    def postprocess(self, raw_output: str, chunks: List):
        warnings = []
        answer = clean_text(raw_output)

        # 1) extract citations
        cited_ids = re.findall(r"\[([^\]]+)\]", answer)
        valid_ids = {c.chunk_id for c in chunks}

        used_chunk_ids = []
        for cid in cited_ids:
            if cid not in valid_ids:
                warnings.append(f"unknown_citation:{cid}")
            else:
                if cid not in used_chunk_ids:
                    used_chunk_ids.append(cid)

        # 2) Fact check sentences
        sentences = sentence_tokenize(answer)
        unsupported_count = 0

        supported_sentences = []
        for s in sentences:
            if self.is_supported(s, chunks):
                supported_sentences.append(s)
            else:
                warnings.append("unsupported_claim")
                supported_sentences.append("I don't know.")
                unsupported_count += 1

        # If too many unsupported
        if len(sentences) > 0 and unsupported_count / len(sentences) >= 0.20:
            return "INSUFFICIENT_CONTEXT", [], warnings

        final_answer = " ".join(supported_sentences)
        return final_answer, used_chunk_ids, warnings

    # ---------------------------------------------------------
    # SUPPORT CHECKER
    # ---------------------------------------------------------
    def is_supported(self, sentence: str, chunks: List) -> bool:
        sent = sentence.lower()
        for c in chunks:
            if token_overlap(sent, c.text.lower()) > 0.30:
                return True
        return False

    # ---------------------------------------------------------
    # CONFIDENCE CALCULATION
    # ---------------------------------------------------------
    def compute_confidence(self, used_ids, chunks, warnings):
        if not used_ids:
            return 0.0

        scores = []
        chunk_map = {c.chunk_id: c for c in chunks}
        for cid in used_ids:
            if cid in chunk_map:
                scores.append(chunk_map[cid].score)

        if not scores:
            return 0.0

        base = sum(scores) / len(scores)

        # penalties
        if any("unsupported_claim" in w for w in warnings):
            base -= 0.20
        if any("unknown_citation" in w for w in warnings):
            base -= 0.05

        return max(0.0, min(1.0, base))
    