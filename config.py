FIXED_CHUNK_SIZE = 512
FIXED_CHUNK_OVERLAP = 52  # 10% of 512

EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4"

DOCUMENTS = {
    "aws": "AWS.pdf",
    "faqs": "FAQs.pdf"
}

DEPARTMENT = "Engineering"

MAX_LEXICAL_RESULTS = 20
MAX_DENSE_RESULTS = 20

# Retrieval Configuration
RRF_SMOOTHING_CONSTANT = 60
RRF_TOP_N_CANDIDATES = 3

# API Configuration
API_HOST = "0.0.0.0"
API_PORT = 8000
API_WORKERS = 4
API_RELOAD = True

# Fallback Message (Hallucination Control)
FALLBACK_MESSAGE = "I am sorry, but I cannot confidently deduce an answer based on the verified technical documentation provided."

# System Prompt Template
SYSTEM_PROMPT_TEMPLATE = """You are an elite Cloud Infrastructure Auditing Specialist. Answer the user query using ONLY the verified context text pieces provided below. If the answer cannot be confidently deduced from the context, respond with your exact fallback text pattern.

Context:
{context}

User Query: {query}"""