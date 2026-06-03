import React from 'react';
import '../styles/SourceAttribution.css';

/**
 * Displays source documents and chunks that contributed to the answer
 * Critical for production RAG - users need to know where answers come from
 */
function SourceAttribution({ sources, confidenceScore }) {
  if (!sources || sources.length === 0) {
    return null;
  }

  const getConfidenceLabel = (score) => {
    if (score < 0.5) return 'Low Confidence';
    if (score < 0.75) return 'Medium Confidence';
    if (score < 0.9) return 'High Confidence';
    return 'Very High Confidence';
  };

  const getConfidenceColor = (score) => {
    if (score < 0.5) return 'confidence-low';
    if (score < 0.75) return 'confidence-medium';
    if (score < 0.9) return 'confidence-high';
    return 'confidence-very-high';
  };

  return (
    <div className="source-attribution">
      <div className="sources-header">
        <span className="sources-label">📄 Sources</span>
        {confidenceScore && (
          <span className={`confidence-badge ${getConfidenceColor(confidenceScore)}`}>
            {getConfidenceLabel(confidenceScore)} ({(confidenceScore * 100).toFixed(0)}%)
          </span>
        )}
      </div>

      <div className="sources-list">
        {sources.map((source, idx) => (
          <div key={idx} className="source-item">
            <div className="source-document">
              <span className="document-icon">📋</span>
              <span className="document-name">{source.document}</span>
            </div>
            <div className="source-details">
              <small className="chunk-id">Chunk: {source.chunk_id}</small>
              {source.relevance_score && (
                <small className="relevance-score">
                  Match: {(source.relevance_score * 100).toFixed(0)}%
                </small>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default SourceAttribution;
