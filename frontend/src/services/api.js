/**
 * API Service Layer
 * Handles all backend communication with Engineer 5 RAG backend
 */

const API_BASE = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';

const api = {
  /**
   * Send a query to the backend and get a grounded answer with sources
   * @param {string} userQuery - The user's question
   * @param {object} metadataFilter - Optional metadata filter (e.g., { department: 'Engineering' })
   * @returns {Promise<{answer: string, citations: Array, status: string, confidence_score: number}>}
   */
  query: async (userQuery, metadataFilter = null) => {
    try {
      console.log(`[API] Calling ${API_BASE}/api/v1/search`);
      const response = await fetch(`${API_BASE}/api/v1/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_query: userQuery,
          metadata_filter: metadataFilter,
        }),
      });

      console.log(`[API] Response status: ${response.status}`);

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`[API] Error response: ${errorText}`);
        throw new Error(`API error: ${response.statusText}`);
      }

      const data = await response.json();
      console.log(`[API] Data received:`, data);

      // Convert backend format (context_chunks) to frontend format (sources)
      return {
        answer: data.answer,
        sources: (data.context_chunks || []).map(chunk => ({
          document: chunk.source_document,
          chunk_id: chunk.chunk_id,
          relevance_score: chunk.rrf_score,
          text_snippet: chunk.text_content,
        })),
        status: 'success',
        confidence_score: 0.85,
        telemetry: data.telemetry || null,
      };
    } catch (error) {
      console.error(`[API] Query failed:`, error.message);
      throw error;
    }
  },

  /**
   * Health check endpoint with retry
   * @returns {Promise<{status: string}>}
   */
  health: async () => {
    const maxRetries = 3;
    let lastError;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        console.log(`[API] Health check attempt ${attempt}/${maxRetries}: ${API_BASE}/health`);

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);

        const response = await fetch(`${API_BASE}/health`, {
          method: 'GET',
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        console.log(`[API] Health check status: ${response.status}`);
        if (!response.ok) {
          throw new Error(`Health check failed: ${response.statusText}`);
        }
        const data = await response.json();
        console.log(`[API] Health check passed`);
        return data;
      } catch (error) {
        lastError = error;
        console.error(`[API] Health check attempt ${attempt} failed:`, error.message);
        if (attempt < maxRetries) {
          await new Promise(resolve => setTimeout(resolve, 500));
        }
      }
    }

    throw lastError;
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
      'aws':
        'Amazon Web Services (AWS) is a comprehensive, evolving cloud computing platform provided by Amazon that includes a mixture of infrastructure as a service (IaaS), platform as a service (PaaS), and packaged software as a service (SaaS) offerings. AWS serves as a reliable, scalable, and cost-effective platform for individuals, start-ups, and enterprises.',
      'components':
        'The main components of AWS include: (1) Compute Services - EC2 (Elastic Compute Cloud), Lambda, Auto Scaling; (2) Storage Services - S3 (Simple Storage Service), EBS (Elastic Block Store), Glacier; (3) Database Services - RDS, DynamoDB; (4) Networking - VPC (Virtual Private Cloud), CloudFront, Route 53; (5) Application Services - SNS, SQS, SES; (6) Developer Tools - AWS CloudFormation, AWS CodeDeploy.',
      's3':
        'Amazon S3 (Simple Storage Service) is object storage with a simple web service interface to store and retrieve any amount of data from anywhere on the web. The default storage class in Amazon S3 is STANDARD, which provides high durability, availability, and performance object storage for general-purpose use.',
      'default':
        'I found information about AWS and cloud services. To get more specific help, try asking about: What is AWS, main components of AWS, or storage classes in S3.',
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
          document: 'AWS.pdf',
          chunk_id: 'aws_001',
          relevance_score: scores[0],
        },
        {
          document: 'AWS.pdf',
          chunk_id: 'aws_002',
          relevance_score: scores[1],
        },
        {
          document: 'FAQs.pdf',
          chunk_id: 'faq_001',
          relevance_score: scores[2],
        },
      ],
      status: 'success',
      confidence_score: scores[0],
    };
  },
};

export default api;
