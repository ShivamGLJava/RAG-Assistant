from typing import List, Dict, Any
import os

class GenerationService:
    def __init__(self, threshold: float = 0.015):
        self.threshold = threshold
        self.hf_token = os.getenv("HF_TOKEN")

    def generate_answer(self, query: str, context_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generates a grounded answer or refuses if confidence is low.
        """
        # Hallucination Guardrail Check
        if not context_chunks or context_chunks[0].get("rrf_score", 1.0) < self.threshold:
            return {
                "answer": "Insufficient information found in the enterprise knowledge base to provide a reliable answer. Please consult the engineering team directly.",
                "citations": [],
                "trusted": False
            }

        # Format context for the prompt
        context_text = "\n\n".join([
            f"Source: {c['metadata']['source']}\nContent: {c['content']}" 
            for c in context_chunks
        ])

        # Construct the Prompt
        prompt = f"""
        System: You are an Enterprise Support Copilot. Answer the query ONLY using the provided context.
        If the answer is not in the context, say you don't know. 
        Always cite your source filename.

        Context:
        {context_text}

        Query: {query}
        Answer:
        """

        # TODO: Call Hugging Face Inference API or similar here
        return {
            "answer": "Answer generated from context (Integration pending)",
            "citations": [
                {"document_name": c["metadata"]["source"], "text_snippet": c["content"]}
                for c in context_chunks
            ],
            "trusted": True
        }
