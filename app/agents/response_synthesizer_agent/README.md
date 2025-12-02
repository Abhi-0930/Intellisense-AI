📘 Response Synthesizer Agent — Full Documentation

The Response Synthesizer Agent is the final stage of your Agentic RAG pipeline.
Its job is to convert retrieved knowledge chunks + user intent into a clean, grounded, safe, citation-rich final answer.

This agent enforces:

✔ Zero hallucinations
✔ Strict citation control
✔ Token-budget-aware context building
✔ Inline evidence linking
✔ Contradiction detection
✔ Confidence estimation
✔ Clean fallback messages

🧩 What This Agent Does

Given the output of your Retrieval Orchestrator (ranked chunks), and the user’s query:

The Response Synthesizer Agent:

Takes in a structured SynthesisInput

Selects only the most relevant chunks (token-budgeted)

Builds a complete context section

Constructs a System + Instruction + Context + User prompt

Calls the LLM

Removes unsupported claims

Validates citations

Detects contradictions

Computes confidence score

Returns a SynthesisOutput with safe, grounded, formatted text

This is the “final brain” before your answer is shown to the user.

📂 Directory Structure
response_synthesizer_agent/
│
├── synthesizer.py     # Main agent engine (LLM call, context, postprocessing)
├── schema.py          # Pydantic models (SynthesisInput, SynthesisOutput)
├── prompts.py         # System + Instruction prompt templates
├── utils.py           # Token estimator, cleaners, sentence splitter
└── tests/
    └── test_synthesizer.py   # Unit tests using a mock LLM

🏗️ System Architecture Overview
Input

SynthesisInput contains:

trace_id

query

retrieved_chunks (from retrieval orchestrator)

preferences (tone, length, citations etc.)

conversation_history

model_name, max_output_tokens

Output

SynthesisOutput contains:

answer

used_chunk_ids

confidence

warnings

raw_model_output

metrics

🔥 End-to-End Execution Stages

Below is the complete flow implemented in synthesizer.py.

🟦 1. Input Validation

Ensures trace_id and query exist.

Ensures retrieved_chunks is a list.

If chunks list is empty → returns fallback:

"I don’t have any information on that..."


No LLM call is made in this case.

🟨 2. Chunk Selection (Token Budgeting)

The synthesizer must use only enough chunk text that the model can fit.
This step:

Sorts chunks by final score

Computes available context tokens

Adds chunks until budget full

If a chunk is too long → creates a highly relevant excerpt using:

sentence tokenization

scoring sentences by keyword overlap

Example:

Chunk text     → 750 tokens
Excerpt used   → 150 tokens (top 3 relevant sentences)


This ensures stable operation even on smaller models.

🟩 3. Context Block Construction

Chunks are converted into readable sections:

CHUNK HEADER: [CHUNK 0] | source_url | chunk_id
CHUNK BODY:
<text>
METADATA:
...
---END CHUNK---


You also get:

Context summary: N chunks included; top_topics: ...


Everything is wrapped in:

CONTEXT_START
<blocks>
CONTEXT_END


This is critical for model grounding.

🟥 4. Prompt Construction

A full LLM prompt consists of:

SYSTEM_PROMPT

INSTRUCTION_PROMPT

CONTEXT_START ... CONTEXT_END

User query

Preferences

Conversation history

This ensures reproducible, controlled LLM behavior.

🟧 5. LLM Call

The agent then calls your ChatGroq model:

temperature=0.0

max_tokens = input.max_output_tokens or 512

model = model_name from input or config

If the model outputs "INSUFFICIENT_CONTEXT" literally → return fallback message.

🟪 6. Postprocessing (Hallucination Guard)

This is one of the strongest parts of this agent.

It performs:

Citation extraction

Citation validation

Sentence-level fact checking

Unsupported claim removal

Contradiction detection

If more than 20% of sentences cannot be verified from chunks:

→ It automatically switches to:

INSUFFICIENT_CONTEXT

This means NO hallucinations are allowed.

Everything must be backed by retrieved text.

🟫 7. Confidence Scoring

Confidence is computed using:

Average score of used chunks

Penalties for:

unsupported claims

unknown citations

contradictions

The score is clamped to [0.0, 1.0].

This enables downstream logic like:

Low confidence → ask user for clarifications

High confidence → proceed

⬛ 8. SynthesisOutput Creation

You get a complete structured object with:

final answer

citations

confidence score

list of warnings

LLM raw response

latency + token usage

This is the final output your UI will show.

💡 Why This Agent Is Special
🔒 100% Hallucination-Controlled

Sentences with no supporting evidence are replaced with:

"I don't know."

📚 Fully Grounded

Every evidence bullet uses:

[chunk_id]

🧠 Smart Context Compression

Large chunks → converted to sharp, relevant excerpts automatically.

📉 Robust Confidence Score

Confidence is not from the LLM — it is computed from evidence.

🔍 Fully Traceable

Context hash + prompt hash logged for reproducibility.

🧪 Testing Your Agent

The included test suite covers:

Empty context scenario

Direct factual extraction

Citation extraction

Unsupported claim removal

Token overflow handling

Run:

pytest app/agents/response_synthesizer_agent/tests/

🛠️ How to Integrate with Retrieval Orchestrator

Your orchestrator must provide:

SynthesisInput(
    trace_id=retrieval_output.trace_id,
    query=user_query,
    retrieved_chunks=retrieval_output.chunks,
    preferences=user_preferences,
    conversation_history=history,
)


Then:

response = await response_synthesizer.run(synthesis_input)
return response.answer

⚙️ Model Configuration

In your config:

class ModelConfig:
    model_name = "mixtral-8x7b"
    max_context_tokens = 8192


You can use:

Groq Mixtral

Groq LLaMA 3

Groq Gemma

OpenAI o4-mini

Any Chat model

📦 Extending the System

Here are built-in extension points:

🔹 Add a Verifier Model

Use a small model to double-check final answer.

🔹 Add a Second Pass (Mode B Agentic)

Use your model to generate a plan, then re-generate final answer.

🔹 Add style transformers

Examples:

academic mode

kids explanation mode

bullet-only answer

JSON-only answer

🔹 Add throttling & caching

LLM prompts are hashable → perfect for caching.

🐞 Debugging Tips
1. Check context_hash

If answers differ on same input → context differs.

2. Check warnings

"unsupported_claim" → model tried to hallucinate

"unknown_citation" → model fabricated chunk ids

"contradictory_sources" → retrieval issue

"truncated_explanation" → user preference max length hit

3. Check token usage

If token usage spikes → context blocks too large.