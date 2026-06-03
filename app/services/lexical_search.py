def keyword_search(query):
    """
    Performs keyword-based lexical search on a document corpus.
    Returns a list of results with chunk_id, text_content, and metadata.
    """
    corpus = {
        1: {
            "text": "To fix a 502 Bad Gateway error, check your upstream server status and verify network connectivity.",
            "source": "troubleshooting_guide.md"
        },
        2: {
            "text": "Container CrashLoopBackOff occurs when your pod fails to start. Check logs with kubectl logs.",
            "source": "kubernetes_handbook.md"
        },
        3: {
            "text": "A 502 error indicates the gateway received an invalid response. Restart your backend services.",
            "source": "error_codes.md"
        },
        4: {
            "text": "Kubernetes debugging: inspect pod status and resource limits to resolve CrashLoopBackOff.",
            "source": "k8s_debugging.md"
        },
        5: {
            "text": "HTTP status codes: 502 Bad Gateway means upstream service unavailable or misconfigured.",
            "source": "http_reference.md"
        }
    }

    keywords = query.lower().split()
    results = []

    for chunk_id, doc in corpus.items():
        text_lower = doc["text"].lower()
        match_count = sum(1 for kw in keywords if kw in text_lower)

        if match_count > 0:
            results.append({
                "chunk_id": chunk_id,
                "text_content": doc["text"],
                "metadata": {"source": doc["source"], "relevance_score": match_count / len(keywords)}
            })

    results.sort(key=lambda x: x["metadata"]["relevance_score"], reverse=True)
    return results
