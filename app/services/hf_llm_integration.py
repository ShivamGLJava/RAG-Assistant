"""
Hugging Face Inference API Integration - Engineer 5 (Orchestration)
Uses Hugging Face's free inference API for text generation.
"""

import os
import requests
from typing import List, Dict, Any, Optional
from pathlib import Path

# Load .env file from project root
def _load_env():
    """Load environment variables from .env file"""
    try:
        # Try multiple possible paths for .env
        possible_paths = [
            Path(__file__).resolve().parent.parent.parent / ".env",
            Path.cwd() / ".env",
            Path("/c/Users/l.venkat/Desktop/RAG-Assistant/.env"),
        ]

        for env_path in possible_paths:
            if env_path.exists():
                print(f"[HF] Loading .env from: {env_path}")
                with open(env_path, encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            key = key.strip()
                            value = value.strip()
                            os.environ[key] = value
                            if key == "HF_API_TOKEN":
                                print(f"[HF] Token loaded: {value[:15]}...{value[-5:]}")
                return

        print("[HF] WARNING: .env file not found in any location")
    except Exception as e:
        print(f"[HF] ERROR loading .env: {e}")

_load_env()


class HuggingFaceLLM:
    """
    Client for Hugging Face Inference API.
    Uses free tier models for grounded answer generation.
    """

    # Configuration
    HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")
    HF_API_URL = "https://api-inference.huggingface.co/models"
    # Using Mistral-7B - fast, good for technical support, free tier available
    MODEL = os.getenv("HF_MODEL", "mistralai/Mistral-7B-Instruct-v0.1")
    TIMEOUT = 60  # seconds

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
        Generate answer from Hugging Face using provided context.

        Args:
            question: User's question
            context: Retrieved context chunks (formatted)

        Returns:
            Generated answer string, or None if error
        """
        try:
            if not HuggingFaceLLM.HF_API_TOKEN:
                print("[ERROR] HF_API_TOKEN environment variable not set")
                print("Get free API token from: https://huggingface.co/settings/tokens")
                return None

            # Build complete prompt
            prompt = HuggingFaceLLM.PROMPT_TEMPLATE.format(
                system_prompt=HuggingFaceLLM.SYSTEM_PROMPT,
                context=context,
                question=question
            )

            # Call Hugging Face Inference API
            headers = {"Authorization": f"Bearer {HuggingFaceLLM.HF_API_TOKEN}"}
            response = requests.post(
                f"{HuggingFaceLLM.HF_API_URL}/{HuggingFaceLLM.MODEL}",
                headers=headers,
                json={
                    "inputs": prompt,
                    "parameters": {
                        "max_length": 500,
                        "temperature": 0.3,  # Low temperature for factual answers
                        "top_p": 0.95,
                        "do_sample": True,
                    }
                },
                timeout=HuggingFaceLLM.TIMEOUT
            )

            if response.status_code != 200:
                print(f"[ERROR] Hugging Face API error: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                return None

            result = response.json()

            # Extract answer from response
            if isinstance(result, list) and len(result) > 0:
                answer = result[0].get("generated_text", "").strip()
                # Remove the prompt from the generated text
                if answer.startswith(prompt):
                    answer = answer[len(prompt):].strip()
            else:
                answer = ""

            if not answer:
                print("[ERROR] Hugging Face returned empty response")
                return None

            return answer

        except requests.ConnectionError:
            print("[ERROR] Cannot connect to Hugging Face API")
            print("Check your internet connection and API token")
            return None
        except requests.Timeout:
            print(f"[ERROR] Hugging Face request timed out after {HuggingFaceLLM.TIMEOUT}s")
            return None
        except Exception as e:
            print(f"[ERROR] Hugging Face integration error: {str(e)}")
            return None

    @staticmethod
    def build_context(chunks: List[Dict[str, Any]]) -> str:
        """
        Formats retrieved chunks into context string for prompt injection.

        Args:
            chunks: List of retrieved chunks with content and metadata

        Returns:
            Formatted context string for LLM
        """
        context_parts = []

        for i, chunk in enumerate(chunks, 1):
            source = chunk.get("metadata", {}).get("source_document", "Unknown")
            content = chunk.get("text_content", "")
            chunk_id = chunk.get("chunk_id", "")

            # Format each chunk with source attribution
            formatted = f"[Source {i}: {source} - {chunk_id}]\n{content}"
            context_parts.append(formatted)

        return "\n\n---\n\n".join(context_parts)

    @staticmethod
    def is_available() -> bool:
        """
        Checks if Hugging Face API is available and token is valid.

        Returns:
            True if API is reachable and token is set, False otherwise
        """
        try:
            if not HuggingFaceLLM.HF_API_TOKEN:
                return False

            headers = {"Authorization": f"Bearer {HuggingFaceLLM.HF_API_TOKEN}"}
            response = requests.get(
                "https://huggingface.co/api/whoami",
                headers=headers,
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False

    @staticmethod
    def get_model_info() -> Dict[str, Any]:
        """
        Get information about configured model.

        Returns:
            Dict with model info or empty dict if unavailable
        """
        try:
            if not HuggingFaceLLM.HF_API_TOKEN:
                return {"error": "API token not set"}

            headers = {"Authorization": f"Bearer {HuggingFaceLLM.HF_API_TOKEN}"}
            response = requests.get(
                f"https://huggingface.co/api/models/{HuggingFaceLLM.MODEL}",
                headers=headers,
                timeout=5
            )
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return {}


# Convenience functions for direct use
def generate_answer(question: str, context: str) -> Optional[str]:
    """
    Generate answer using Hugging Face with provided context.

    Args:
        question: User's question
        context: Retrieved context

    Returns:
        Generated answer or None if error
    """
    return HuggingFaceLLM.query(question, context)


def format_context(chunks: List[Dict[str, Any]]) -> str:
    """
    Format chunks into context string.

    Args:
        chunks: List of retrieved chunks

    Returns:
        Formatted context string
    """
    return HuggingFaceLLM.build_context(chunks)


def check_hf_ready() -> bool:
    """
    Check if Hugging Face is ready to use.

    Returns:
        True if HF API is available and token is set
    """
    return HuggingFaceLLM.is_available()
