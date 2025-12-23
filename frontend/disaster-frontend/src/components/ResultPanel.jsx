import React from 'react';
import SkeletonLoader from './SkeletonLoader';

function ResultPanel({ result, loading }) {
  if (loading) {
    return <SkeletonLoader type="card" count={1} />;
  }

  if (!result) {
    return (
      <div className="card result-card">
        <div className="card-header">
          <h2>📊 Analysis Results</h2>
          <p className="subtitle">Analyze a tweet to see detailed results</p>
        </div>
        <div className="empty-state">
          <div className="empty-icon">🔍</div>
          <p>No tweet analyzed yet. Enter a tweet above to get started.</p>
        </div>
      </div>
    );
  }

  const {
    tweet,
    disaster_text,
    disaster_label,
    confidence,
    confidence_percentage,
    disaster_probability,
    category,
    severity,
    risk_level,
    location,
    location_mention,
    lat,
    lon,
    model_info,
  } = result;

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'High':
        return '#ef4444';
      case 'Medium':
        return '#f59e0b';
      case 'Low':
        return '#22c55e';
      default:
        return '#6b7280';
    }
  };

  const getRiskColor = (risk) => {
    switch (risk) {
      case 'Critical':
        return '#dc2626';
      case 'High':
        return '#ef4444';
      case 'Medium':
        return '#f59e0b';
      case 'Low':
        return '#22c55e';
      default:
        return '#6b7280';
    }
  };

  return (
    <div className="card result-card" style={{ animation: 'fadeIn 0.5s ease' }}>
      <div className="card-header">
        <h2>📊 Analysis Results</h2>
        <p className="subtitle">Detailed classification and insights</p>
      </div>

      <div className="result-content">
        {/* Classification Status - Prominent */}
        <div className="result-section" style={{ 
          background: disaster_label 
            ? 'linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.1) 100%)'
            : 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%)',
          borderColor: disaster_label ? 'rgba(239, 68, 68, 0.3)' : 'rgba(16, 185, 129, 0.3)'
        }}>
          <label className="section-label">🎯 Classification</label>
          <div className={`status-badge ${disaster_label ? 'disaster' : 'safe'}`}>
            <span className="status-icon">{disaster_label ? '🚨' : '✅'}</span>
            <span className="status-text">{disaster_text}</span>
          </div>
        </div>

        {/* Tweet Text */}
        <div className="result-section">
          <label className="section-label">📝 Tweet Text</label>
          <div className="tweet-text">{tweet}</div>
        </div>

        {/* Confidence Score */}
        <div className="result-section">
          <label className="section-label">📈 Confidence Score</label>
          <div className="confidence-display">
            <div className="confidence-bar-container">
              <div
                className="confidence-bar"
                style={{
                  width: `${confidence_percentage || confidence * 100}%`,
                  background: disaster_label 
                    ? 'linear-gradient(90deg, #ef4444 0%, #dc2626 100%)'
                    : 'linear-gradient(90deg, #10b981 0%, #059669 100%)',
                }}
              />
            </div>
            <div className="confidence-text">
              <strong style={{ fontSize: '1.3rem' }}>
                {confidence_percentage || (confidence * 100).toFixed(1)}%
              </strong>
              {disaster_probability !== undefined && (
                <span className="probability">
                  (Disaster Probability: {disaster_probability}%)
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Category and Severity */}
        <div className="metrics-grid">
          <div className="metric-item">
            <label className="metric-label">🏷️ Disaster Category</label>
            <div className="metric-value category-badge">{category}</div>
          </div>
          <div className="metric-item">
            <label className="metric-label">⚡ Severity Level</label>
            <div
              className="metric-value severity-badge"
              style={{ backgroundColor: getSeverityColor(severity) }}
            >
              {severity}
            </div>
          </div>
        </div>

        {/* Risk Assessment */}
        {risk_level && (
          <div className="result-section">
            <label className="section-label">⚠️ Risk Assessment</label>
            <div
              className="risk-badge"
              style={{ backgroundColor: getRiskColor(risk_level) }}
            >
              {risk_level} Risk
            </div>
          </div>
        )}

        {/* Location Information */}
        <div className="result-section">
          <label className="section-label">📍 Location Information</label>
          <div className="location-info">
            {location_mention && (
              <div className="info-row">
                <span className="info-label">Detected Location:</span>
                <span className="info-value">{location_mention}</span>
              </div>
            )}
            {location && (
              <div className="info-row">
                <span className="info-label">Geocoded Location:</span>
                <span className="info-value">{location}</span>
              </div>
            )}
            {lat && lon && (
              <div className="info-row">
                <span className="info-label">Coordinates:</span>
                <span className="info-value coordinates">
                  {lat.toFixed(4)}, {lon.toFixed(4)}
                </span>
              </div>
            )}
            {!location_mention && !location && (
              <div className="info-row">
                <span className="info-value no-location">
                  No location detected in tweet
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Model Information */}
        {model_info && (
          <div className="result-section model-info">
            <label className="section-label">🤖 Model Information</label>
            <div className="model-stats">
              <div className="model-stat">
                <span className="stat-label">Model:</span>
                <span className="stat-value">
                  {model_info.model_name || 'Unknown'}
                </span>
              </div>
              {model_info.accuracy && (
                <div className="model-stat">
                  <span className="stat-label">Accuracy:</span>
                  <span className="stat-value">
                    {(model_info.accuracy * 100).toFixed(1)}%
                  </span>
                </div>
              )}
              {model_info.f1_score && (
                <div className="model-stat">
                  <span className="stat-label">F1-Score:</span>
                  <span className="stat-value">
                    {(model_info.f1_score * 100).toFixed(1)}%
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ResultPanel;




