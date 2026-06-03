"""
Mock RRF Service - Engineer 5 (Orchestration)
Generates mock Reciprocal Rank Fusion results for testing.
Will be replaced with Engineer 4's real RRF implementation when ready.
"""

from typing import List, Dict, Any
import random


# Mock knowledge base with realistic technical support content
MOCK_KNOWLEDGE_BASE = {
    "crashloopbackoff": [
        {
            "chunk_id": "doc_002_chk_3",
            "text_content": "Container CrashLoopBackOff occurs when your pod fails to start repeatedly. This typically indicates an issue with your container configuration, application code, or resource constraints. Check your pod logs with `kubectl logs <pod-name>` to see the actual error message. Common causes include: incorrect image name, missing environment variables, unmet resource requirements, or application startup failures.",
            "metadata": {
                "source_document": "kubernetes_handbook.md",
                "source": "kubernetes_handbook.md",
                "department": "Engineering",
                "chunk_size": 512
            },
            "rrf_score": 0.95
        },
        {
            "chunk_id": "doc_004_chk_1",
            "text_content": "Kubernetes debugging: inspect pod status and resource limits to resolve CrashLoopBackOff. Use `kubectl describe pod <pod-name>` to get detailed information about pod events, conditions, and resource requests. Check container logs with `kubectl logs --previous <pod-name>` to see logs from the previous container run if the current one crashed.",
            "metadata": {
                "source_document": "k8s_debugging.md",
                "source": "k8s_debugging.md",
                "department": "Engineering",
                "chunk_size": 512
            },
            "rrf_score": 0.88
        },
        {
            "chunk_id": "doc_003_chk_2",
            "text_content": "Pod restart loops (CrashLoopBackOff) are often caused by: 1) Application throwing uncaught exceptions 2) Missing required environment variables 3) Volume mount failures 4) Insufficient CPU/memory allocation 5) Incompatible container base image. Debug by checking logs, event descriptions, and resource utilization metrics.",
            "metadata": {
                "source_document": "troubleshooting_guide.md",
                "source": "troubleshooting_guide.md",
                "department": "Engineering",
                "chunk_size": 512
            },
            "rrf_score": 0.81
        }
    ],
    "502": [
        {
            "chunk_id": "doc_001_chk_1",
            "text_content": "To fix a 502 Bad Gateway error, check your upstream server status and verify network connectivity. A 502 error means the gateway or proxy server received an invalid response from an upstream server. First, verify that your backend services are running and healthy. Check service logs for errors. Ensure DNS resolution is working correctly and firewall rules allow traffic.",
            "metadata": {
                "source_document": "troubleshooting_guide.md",
                "source": "troubleshooting_guide.md",
                "department": "Engineering",
                "chunk_size": 512
            },
            "rrf_score": 0.93
        },
        {
            "chunk_id": "doc_005_chk_2",
            "text_content": "HTTP status codes: 502 Bad Gateway means upstream service unavailable or misconfigured. The server is acting as a gateway or proxy and received an invalid response from the upstream server. Common causes: backend server down, connection timeout, proxy misconfiguration, SSL/TLS handshake failure, or malformed backend response.",
            "metadata": {
                "source_document": "http_reference.md",
                "source": "http_reference.md",
                "department": "Engineering",
                "chunk_size": 512
            },
            "rrf_score": 0.85
        },
        {
            "chunk_id": "doc_006_chk_3",
            "text_content": "502 gateway errors debugging: Check upstream server logs. Verify service is listening on expected port. Test connectivity: curl localhost:port. Check proxy configuration for correct backend addresses. Monitor resource utilization (CPU, memory, disk). Review firewall and security group rules. Test with health check endpoints.",
            "metadata": {
                "source_document": "http_reference.md",
                "source": "http_reference.md",
                "department": "Engineering",
                "chunk_size": 512
            },
            "rrf_score": 0.79
        }
    ],
    "imagepullbackoff": [
        {
            "chunk_id": "doc_007_chk_1",
            "text_content": "ImagePullBackOff error means Kubernetes cannot pull your container image. This usually happens when: 1) Image doesn't exist in the registry 2) Registry is unavailable 3) Authentication fails 4) Wrong image name or tag. Verify the image name and tag are correct. Check that the image registry is accessible. If using a private registry, ensure your imagePullSecret is properly configured.",
            "metadata": {
                "source_document": "kubernetes_handbook.md",
                "source": "kubernetes_handbook.md",
                "department": "Engineering",
                "chunk_size": 512
            },
            "rrf_score": 0.92
        },
        {
            "chunk_id": "doc_008_chk_2",
            "text_content": "Check ImagePullBackOff events: Run `kubectl describe pod <pod-name>` to see event messages. Check event details for authentication errors or 'image not found'. Verify image registry URL. Test image pull manually: `docker pull <image>`. Ensure kubelet has access to image registry. Check imagePullSecrets in pod spec.",
            "metadata": {
                "source_document": "k8s_debugging.md",
                "source": "k8s_debugging.md",
                "department": "Engineering",
                "chunk_size": 512
            },
            "rrf_score": 0.86
        },
        {
            "chunk_id": "doc_009_chk_3",
            "text_content": "Docker image pull authentication: For private registries, create imagePullSecret with: kubectl create secret docker-registry <secret-name> --docker-server=<registry> --docker-username=<user> --docker-password=<pass>. Reference secret in pod spec: imagePullSecrets: [{name: <secret-name>}]. Verify registry credentials are correct.",
            "metadata": {
                "source_document": "docker_registry_guide.md",
                "source": "docker_registry_guide.md",
                "department": "Engineering",
                "chunk_size": 512
            },
            "rrf_score": 0.78
        }
    ]
}


class MockRRFEngine:
    """
    Generates mock RRF results for testing without Engineer 4's implementation.
    Returns results in the same format as the real RRF engine will.
    """

    @staticmethod
    def search(query: str, top_n: int = 3) -> List[Dict[str, Any]]:
        """
        Mock RRF search - returns relevant chunks based on query keywords.

        Args:
            query: User's search query
            top_n: Number of top results to return (default: 3)

        Returns:
            List of ranked chunks with RRF scores
        """
        query_lower = query.lower()

        # Match query to knowledge base
        results = []
        if any(keyword in query_lower for keyword in ["crash", "crashloopbackoff", "pod fails", "restart"]):
            results = MOCK_KNOWLEDGE_BASE.get("crashloopbackoff", [])
        elif any(keyword in query_lower for keyword in ["502", "bad gateway", "upstream"]):
            results = MOCK_KNOWLEDGE_BASE.get("502", [])
        elif any(keyword in query_lower for keyword in ["image", "imagepull", "pull"]):
            results = MOCK_KNOWLEDGE_BASE.get("imagepullbackoff", [])
        else:
            # Return default results if no keyword match
            results = _get_default_results()

        # Return top_n results (already scored)
        return results[:top_n]

    @staticmethod
    def search_no_results(query: str) -> List[Dict[str, Any]]:
        """
        Mock RRF search that returns no results - for testing firewall.
        Used to test hallucination prevention when knowledge base has no answer.
        """
        return []

    @staticmethod
    def search_low_confidence(query: str) -> List[Dict[str, Any]]:
        """
        Mock RRF search with low confidence scores - for testing firewall.
        Used to test that firewall blocks answers with low confidence.
        """
        return [
            {
                "chunk_id": "doc_unknown_chk_1",
                "text_content": "Marginally relevant text that doesn't really answer the question.",
                "metadata": {
                    "source_document": "unknown.md",
                    "source": "unknown.md",
                    "department": "Engineering",
                    "chunk_size": 512
                },
                "rrf_score": 0.05  # Below threshold (0.1)
            }
        ]


def _get_default_results() -> List[Dict[str, Any]]:
    """
    Default mock results when no keyword matches.
    Provides generic technical troubleshooting guidance.
    """
    return [
        {
            "chunk_id": "doc_general_chk_1",
            "text_content": "For troubleshooting technical issues: 1) Check logs and error messages 2) Verify configuration is correct 3) Test connectivity and dependencies 4) Review recent changes 5) Check resource utilization. If issue persists, contact your infrastructure team or check documentation for specific error codes.",
            "metadata": {
                "source_document": "general_troubleshooting.md",
                "source": "general_troubleshooting.md",
                "department": "Engineering",
                "chunk_size": 512
            },
            "rrf_score": 0.65
        },
        {
            "chunk_id": "doc_general_chk_2",
            "text_content": "Common debugging techniques: Use verbose logging (debug/trace level), add instrumentation to track execution, check system metrics (CPU, memory, disk), review audit logs, test in isolated environment, use diagnostic tools specific to your technology stack.",
            "metadata": {
                "source_document": "debugging_guide.md",
                "source": "debugging_guide.md",
                "department": "Engineering",
                "chunk_size": 512
            },
            "rrf_score": 0.55
        },
        {
            "chunk_id": "doc_general_chk_3",
            "text_content": "Documentation resources: Check official documentation for your framework/tool, search community forums and Stack Overflow, review GitHub issues and discussions, consult internal wiki and runbooks, contact support team.",
            "metadata": {
                "source_document": "documentation_resources.md",
                "source": "documentation_resources.md",
                "department": "Engineering",
                "chunk_size": 512
            },
            "rrf_score": 0.50
        }
    ]


# Public interface for importing
def get_mock_rrf_results(query: str, top_n: int = 3) -> List[Dict[str, Any]]:
    """
    Convenience function to get mock RRF results.
    Can be easily swapped with real RRF implementation.
    """
    return MockRRFEngine.search(query, top_n)
