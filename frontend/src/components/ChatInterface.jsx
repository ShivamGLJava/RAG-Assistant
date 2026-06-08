import React, { useState, useEffect } from 'react';
import MessageList from './MessageList';
import InputField from './InputField';
import TelemetryPanel from './TelemetryPanel';
import api from '../services/api';
import '../styles/ChatInterface.css';

/**
 * Main Chat Interface Component
 * Orchestrates the conversation between user and RAG assistant
 */
function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [backendReady, setBackendReady] = useState(false);
  const [useMockData, setUseMockData] = useState(false);
  const [telemetry, setTelemetry] = useState(null);

  // Check if backend is available on mount
  useEffect(() => {
    const checkBackend = async () => {
      try {
        console.log('[Chat] Checking backend...');
        await api.health();
        console.log('[Chat] Backend is ready!');
        setBackendReady(true);
        setUseMockData(false);
      } catch (error) {
        console.warn('[Chat] Backend not available, using mock data:', error.message);
        setBackendReady(false);
        setUseMockData(true);
      }
    };

    // Wait a moment for backend to be ready, then check
    const timeout = setTimeout(checkBackend, 500);
    return () => clearTimeout(timeout);
  }, []);

  const handleSendQuery = async (userQuery) => {
    // Add user message
    const userMessage = {
      role: 'user',
      content: userQuery,
    };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);
    setTelemetry(null);

    try {
      let response;

      if (useMockData) {
        // Use mock data when backend is not available
        response = await api.mockQuery(userQuery);
      } else {
        // Call real backend
        response = await api.query(userQuery);
      }

      // Extract telemetry data if present
      if (response.telemetry) {
        setTelemetry(response.telemetry);
      }

      // Handle response based on status
      if (response.status === 'no_reliable_answer') {
        // Hallucination firewall blocked the answer
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: response.answer,
            sources: [],
            confidenceScore: response.confidence_score || 0,
            telemetry: response.telemetry || null,
          },
        ]);
      } else if (response.status === 'success') {
        // Normal successful response with LLM answer
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: response.answer,
            sources: response.sources || [],
            confidenceScore: response.confidence_score || 0,
            telemetry: response.telemetry || null,
          },
        ]);
      } else if (response.status === 'error') {
        // Error response (e.g., Ollama not running)
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: `⚠️ ${response.answer}`,
            error: true,
            sources: response.sources || [],
            confidenceScore: response.confidence_score || 0,
            telemetry: response.telemetry || null,
          },
        ]);
      } else {
        // Default case for any status
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: response.answer || 'No response received',
            sources: response.sources || [],
            confidenceScore: response.confidence_score || 0,
            telemetry: response.telemetry || null,
          },
        ]);
      }
    } catch (error) {
      // Network or parsing error
      console.error('Error processing query:', error);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `❌ Error: Unable to process query. ${error.message}. ${
            !useMockData
              ? 'Make sure the backend server is running on http://localhost:8000'
              : ''
          }`,
          error: true,
          sources: [],
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const toggleMockData = () => {
    setUseMockData(!useMockData);
    setMessages([]);
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <div className="header-content">
          <h1>🔧 Technical Support Assistant</h1>
          <p className="tagline">
            Powered by Retrieval-Augmented Generation (RAG)
          </p>
        </div>
        <div className="header-status">
          {backendReady ? (
            <span className="status-badge ready">
              <span className="status-dot"></span> Backend Ready
            </span>
          ) : (
            <button
              className="mode-toggle"
              onClick={toggleMockData}
              title="Toggle between mock data and backend"
            >
              {useMockData ? '📦 Mock Mode' : '🔌 No Backend'}
            </button>
          )}
        </div>
      </div>

      <TelemetryPanel telemetry={telemetry} isLoading={loading} />

      <MessageList messages={messages} />

      <InputField
        onSend={handleSendQuery}
        disabled={false}
        loading={loading}
      />

      {useMockData && (
        <div className="demo-banner">
          <span className="demo-icon">ℹ️</span>
          <span>Using demo data - Connect to backend for real results</span>
        </div>
      )}
    </div>
  );
}

export default ChatInterface;
