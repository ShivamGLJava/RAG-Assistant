"""
Ollama LLM Integration - Engineer 5 (Orchestration)
Connects to local Ollama instance running Llama-3-8B for grounded answer generation.
"""

import os
import requests
from typing import List, Dict, Any, Optional


class OllamaLLM:
    """
    Client for interacting with local Ollama LLM instance.
    Handles prompt engineering, context injection, and error handling.
    """

    # Configuration
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    MODEL = os.getenv("OLLAMA_MODEL", "llama2")
    TIMEOUT = 30  # seconds

    # Prompt templates for strict grounding
    SYSTEM_PROMPT = """You are a technical support assistant for an enterprise knowledge base.

Your role is to answer questions ONLY based on the provided context.

Rules:
1. Only use information from the Context section below
2. Do NOT make up or assume information
3. If the context doesn't contain the answer, respond: "I don't have this information in the knowledge base."
4. Be concise and accurate
5. Keep technical explanations clear
6. Don't speculate or add general knowledge not in context"""

    PROMPT_TEMPLATE = """{system_prompt}

Context:
{context}

Question: {question}

Answer:"""

    @staticmethod
    def query(question: str, context: str) -> Optional[str]:
        """
        Generate answer from Ollama using provided context.
        """
        try:
            # Build complete prompt
            prompt = OllamaLLM.PROMPT_TEMPLATE.format(
                system_prompt=OllamaLLM.SYSTEM_PROMPT,
                context=context,
                question=question
            )

            # Call Ollama API
            response = requests.post(
                f"{OllamaLLM.OLLAMA_URL}/api/generate",
                json={
                    "model": OllamaLLM.MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.3,
                },
                timeout=OllamaLLM.TIMEOUT
            )

            if response.status_code != 200:
                print(f"[ERROR] Ollama API error: {response.status_code}")
                return None

            result = response.json()
            answer = result.get("response", "").strip()

            if not answer:
                print("[ERROR] Ollama returned empty response")
                return None

            return answer

        except requests.ConnectionError:
            print(f"[ERROR] Cannot connect to Ollama at {OllamaLLM.OLLAMA_URL}")
            return None
        except requests.Timeout:
            print(f"[ERROR] Ollama request timed out after {OllamaLLM.TIMEOUT}s")
            return None
        except Exception:
            # Safely catch and isolate malformed local process output
            pass  # nosec
            return None

    @staticmethod
    def build_context(chunks: List[Dict[str, Any]]) -> str:
        """Formats retrieved chunks into context string for prompt injection."""
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get("metadata", {}).get("source_document", "Unknown")
            content = chunk.get("text_content", "")
            chunk_id = chunk.get("chunk_id", "")
            formatted = f"[Source {i}: {source} - {chunk_id}]\n{content}"
            context_parts.append(formatted)
        return "\n\n---\n\n".join(context_parts)

    @staticmethod
    def is_available() -> bool:
        """Checks if Ollama is available and running."""
        try:
            response = requests.get(
                f"{OllamaLLM.OLLAMA_URL}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False

    @staticmethod
    def get_available_models() -> List[str]:
        """Get list of available models in Ollama."""
        try:
            response = requests.get(
                f"{OllamaLLM.OLLAMA_URL}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                return [m.get("name", "") for m in data.get("models", [])]
        except Exception:
            pass  # nosec
        return []

    @staticmethod
    def pull_model(model_name: str) -> bool:
        """Download a model to Ollama if not already present."""
        try:
            response = requests.post(
                f"{OllamaLLM.OLLAMA_URL}/api/pull",
                json={"name": model_name},
                timeout=300
            )
            return response.status_code == 200
        except Exception as e:
            print(f"[ERROR] Failed to pull model {model_name}: {str(e)}")
            return False

    @staticmethod
    def get_model_info() -> Dict[str, Any]:
        """Get information about configured model."""
        try:
            response = requests.post(
                f"{OllamaLLM.OLLAMA_URL}/api/show",
                json={"name": OllamaLLM.MODEL},
                timeout=5
            )
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass  # nosec
        return {}


def generate_answer(question: str, context: str) -> Optional[str]:
    return OllamaLLM.query(question, context)

def format_context(chunks: List[Dict[str, Any]]) -> str:
    return OllamaLLM.build_context(chunks)

def check_ollama_ready() -> bool:
    if not OllamaLLM.is_available():
        return False
    models = OllamaLLM.get_available_models()
    return len(models) > 0