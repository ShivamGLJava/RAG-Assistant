/**
 * API Service Layer
 * Handles all backend communication with Engineer 5 RAG backend
 */

const API_BASE = process.env.REACT_APP_API_URL || 'http://127.0.0.1:7777';

const api = {
  /**
   * Send a query to the backend and get a grounded answer with sources
   * @param {string} userQuery - The user's question
   * @param {object} metadataFilter - Optional metadata filter (e.g., { department: 'Engineering' })
   * @returns {Promise<{answer: string, citations: Array, status: string, confidence_score: number}>}
   */
  query: async (userQuery, metadataFilter = null) => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_query: userQuery,
          metadata_filter: metadataFilter,
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      const data = await response.json();
      // Convert backend format (citations) to frontend format (sources)
      return {
        answer: data.answer,
        sources: (data.citations || []).map(citation => ({
          document: citation.document_name,
          chunk_id: citation.chunk_id,
          relevance_score: citation.relevance_score,
          text_snippet: citation.text_snippet,
        })),
        status: data.status,
        confidence_score: data.confidence_score,
      };
    } catch (error) {
      console.error('Query failed:', error);
      throw error;
    }
  },

  /**
   * Health check endpoint
   * @returns {Promise<{status: string}>}
   */
  health: async () => {
    try {
      const response = await fetch(`${API_BASE}/health`);
      if (!response.ok) {
        throw new Error('Health check failed');
      }
      return response.json();
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  },

  /**
   * For testing: get mock response
   * Useful when backend is not ready
   * @param {string} userQuery - The user's question
   * @returns {Promise<{answer: string, sources: Array, status: string}>}
   */
  mockQuery: async (userQuery) => {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 800));

    // Mock knowledge base
    const mockResponses = {
      'crashloopbackoff':
        'Container CrashLoopBackOff occurs when your pod fails to start repeatedly. This typically indicates an issue with your container configuration. Check your pod logs with `kubectl logs <pod-name>` to see the actual error. Common causes include: incorrect image name, missing environment variables, or resource constraints. Verify your pod resource limits match your application requirements.',
      '502':
        'A 502 Bad Gateway error indicates your upstream server is unavailable or misconfigured. Check that your backend services are running and accessible. Verify network connectivity between your load balancer and backend servers. Check server logs for errors. Ensure DNS resolution is working correctly. You may need to restart services or check firewall rules.',
      'imagepullbackoff':
        'ImagePullBackOff error means Kubernetes cannot pull your container image. This usually happens when the image doesn\'t exist, the registry is unavailable, or authentication fails. Verify the image name and tag are correct. Check that the image registry is accessible. If using a private registry, ensure your imagePullSecret is properly configured. Check the event logs with `kubectl describe pod <pod-name>`.',
      'default':
        'I found information about technical troubleshooting. To get more specific help, try asking about: CrashLoopBackOff, 502 errors, or ImagePullBackOff issues.',
    };

    // Match user query to mock response
    const query = userQuery.toLowerCase();
    let answer =
      Object.entries(mockResponses).find(([key]) => query.includes(key))?.[1] ||
      mockResponses.default;

    // Randomly assign relevance scores
    const scores = [0.92, 0.87, 0.78];

    return {
      answer,
      sources: [
        {
          document: 'kubernetes_handbook.md',
          chunk_id: 'doc_002_chk_3',
          relevance_score: scores[0],
        },
        {
          document: 'troubleshooting_guide.md',
          chunk_id: 'doc_001_chk_1',
          relevance_score: scores[1],
        },
        {
          document: 'k8s_debugging.md',
          chunk_id: 'doc_004_chk_1',
          relevance_score: scores[2],
        },
      ],
      status: 'success',
      confidence_score: scores[0],
    };
  },
};

export default api;
