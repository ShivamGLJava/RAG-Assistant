import React, { useEffect, useRef } from 'react';
import SourceAttribution from './SourceAttribution';
import '../styles/MessageList.css';

/**
 * Displays conversation history with user queries and AI responses
 * Auto-scrolls to latest message for better UX
 */
function MessageList({ messages }) {
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="message-list empty">
        <div className="empty-state">
          <div className="empty-icon">🔍</div>
          <h2>Technical Support Assistant</h2>
          <p>Ask me about technical issues like:</p>
          <ul>
            <li>How do I troubleshoot a CrashLoopBackOff error?</li>
            <li>What causes a 502 Bad Gateway issue?</li>
            <li>How can I resolve an ImagePullBackOff error?</li>
          </ul>
        </div>
      </div>
    );
  }

  return (
    <div className="message-list">
      {messages.map((msg, idx) => (
        <div
          key={idx}
          className={`message-wrapper ${msg.role}`}
        >
          <div className={`message ${msg.role} ${msg.error ? 'error' : ''}`}>
            {msg.role === 'user' ? (
              <div className="user-message-content">{msg.content}</div>
            ) : (
              <div className="assistant-message-content">
                <div className="answer-text">{msg.content}</div>
                {msg.sources && msg.sources.length > 0 && (
                  <SourceAttribution
                    sources={msg.sources}
                    confidenceScore={msg.confidenceScore}
                  />
                )}
              </div>
            )}
          </div>
        </div>
      ))}
      <div ref={messagesEndRef} />
    </div>
  );
}

export default MessageList;
