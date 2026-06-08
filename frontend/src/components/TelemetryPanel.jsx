import React, { useState } from 'react';
import '../styles/TelemetryPanel.css';

const TelemetryPanel = ({ telemetry, isLoading }) => {
  const [isExpanded, setIsExpanded] = useState(true);

  if (!telemetry && !isLoading) {
    return null;
  }

  const toggleExpanded = () => {
    setIsExpanded(!isExpanded);
  };

  const getStageIcon = (stage) => {
    const icons = {
      retrieval: '🔍',
      ranking: '📊',
      firewall: '🛡️',
      llm: '🤖',
      formatting: '✨'
    };
    return icons[stage] || '⚙️';
  };

  const getBottleneckColor = (stage, isBottleneck) => {
    if (!isBottleneck) return '#667eea';
    return '#f56565';
  };

  return (
    <div className="telemetry-panel">
      <div className="telemetry-header" onClick={toggleExpanded}>
        <div className="telemetry-title">
          <span className="telemetry-icon">📡</span>
          <h3>Pipeline Telemetry</h3>
        </div>
        <button className="telemetry-toggle" aria-label="Toggle telemetry panel">
          {isExpanded ? '▼' : '▶'}
        </button>
      </div>

      {isExpanded && (
        <div className="telemetry-content">
          {isLoading ? (
            <div className="telemetry-loading">
              <div className="spinner"></div>
              <p>Processing request...</p>
            </div>
          ) : telemetry ? (
            <>
              <div className="telemetry-summary">
                <div className="summary-item">
                  <span className="summary-label">Total Time</span>
                  <span className="summary-value">{telemetry.total_duration_ms.toFixed(2)}ms</span>
                </div>
                <div className="summary-item">
                  <span className="summary-label">Bottleneck</span>
                  <span className="summary-value bottleneck">{telemetry.bottleneck_stage}</span>
                </div>
                <div className="summary-item">
                  <span className="summary-label">Confidence</span>
                  <span className="summary-value confidence">
                    {(telemetry.firewall_confidence_score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>

              <div className="telemetry-stages">
                <h4>Stage Breakdown</h4>
                <div className="stages-list">
                  {telemetry.timings.map((timing) => {
                    const isBottleneck = timing.stage === telemetry.bottleneck_stage;
                    const percentage = (timing.duration_ms / telemetry.total_duration_ms) * 100;

                    return (
                      <div
                        key={timing.stage}
                        className={`stage-item ${isBottleneck ? 'bottleneck' : ''}`}
                      >
                        <div className="stage-header">
                          <span className="stage-icon">{getStageIcon(timing.stage)}</span>
                          <span className="stage-name">{timing.stage}</span>
                          <span className="stage-duration">{timing.duration_ms.toFixed(2)}ms</span>
                        </div>
                        <div className="stage-bar-container">
                          <div
                            className="stage-bar"
                            style={{
                              width: `${percentage}%`,
                              backgroundColor: getBottleneckColor(timing.stage, isBottleneck),
                              opacity: isBottleneck ? 1 : 0.7
                            }}
                          ></div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="telemetry-confidence">
                <h4>Firewall Confidence Score</h4>
                <div className="confidence-container">
                  <div className="confidence-bar-bg">
                    <div
                      className="confidence-bar-fill"
                      style={{
                        width: `${telemetry.firewall_confidence_score * 100}%`
                      }}
                    ></div>
                  </div>
                  <p className="confidence-text">
                    {telemetry.firewall_confidence_score >= 0.5
                      ? '✓ High confidence in retrieved context'
                      : telemetry.firewall_confidence_score >= 0.01
                      ? '⚠ Moderate confidence in retrieved context'
                      : '✗ Low confidence in retrieved context'}
                  </p>
                </div>
              </div>
            </>
          ) : null}
        </div>
      )}
    </div>
  );
};

export default TelemetryPanel;
