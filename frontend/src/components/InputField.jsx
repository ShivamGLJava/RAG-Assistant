import React, { useState } from 'react';
import '../styles/InputField.css';

/**
 * Input field for user queries
 * Handles text input and submission with loading states
 */
function InputField({ onSend, disabled = false, loading = false }) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && !disabled && !loading) {
      onSend(query.trim());
      setQuery('');
    }
  };

  const handleKeyDown = (e) => {
    // Send on Enter, but allow Shift+Enter for new lines
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="input-container">
      <form onSubmit={handleSubmit} className="query-form">
        <div className="input-wrapper">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a technical question..."
            disabled={disabled || loading}
            className="query-input"
            autoFocus
          />
          <button
            type="submit"
            disabled={!query.trim() || disabled || loading}
            className={`submit-btn ${loading ? 'loading' : ''}`}
            title="Send query (Shift+Enter for new line)"
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Searching...
              </>
            ) : (
              <>
                <span className="send-icon">→</span>
                Send
              </>
            )}
          </button>
        </div>
        <small className="input-hint">
          Press Enter to send • Shift+Enter for new line
        </small>
      </form>
    </div>
  );
}

export default InputField;
