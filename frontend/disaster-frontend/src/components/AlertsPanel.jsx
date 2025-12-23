import React, { useState, useEffect } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

function AlertsPanel() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [clearing, setClearing] = useState(false);

  useEffect(() => {
    fetchAlerts();
    // Refresh alerts every 10 seconds during active use (more frequent)
    const interval = setInterval(fetchAlerts, 10000);
    return () => clearInterval(interval);
  }, []);
  
  // Highlight panel when new alerts are detected
  useEffect(() => {
    if (alerts.length > 0) {
      const panel = document.querySelector('[data-alerts-panel]');
      if (panel) {
        // Pulse animation to draw attention
        panel.style.animation = 'pulse 1s ease 2';
        panel.style.border = '2px solid rgba(220, 38, 38, 0.6)';
        panel.style.boxShadow = '0 0 25px rgba(220, 38, 38, 0.4)';
        
        setTimeout(() => {
          panel.style.animation = '';
          panel.style.border = '';
          panel.style.boxShadow = '';
        }, 2000);
      }
    }
  }, [alerts.length]);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/alerts?min_credibility=0.7`);
      if (!response.ok) throw new Error('Failed to fetch alerts');
      const data = await response.json();
      if (data.status === 'success') {
        setAlerts(data.alerts || []);
      }
      setError(null);
    } catch (err) {
      console.error('Error fetching alerts:', err);
      setError('Failed to load alerts');
    } finally {
      setLoading(false);
    }
  };

  const getAlertColor = (alertLevel) => {
    switch (alertLevel) {
      case 'Critical':
        return '#dc2626';
      case 'High':
        return '#ef4444';
      case 'Medium':
        return '#f59e0b';
      default:
        return '#6b7280';
    }
  };

  const getAlertIcon = (alertLevel) => {
    switch (alertLevel) {
      case 'Critical':
        return '🚨';
      case 'High':
        return '⚠️';
      case 'Medium':
        return '⚡';
      default:
        return 'ℹ️';
    }
  };

  const handleClearData = async () => {
    if (!showClearConfirm) {
      setShowClearConfirm(true);
      return;
    }

    try {
      setClearing(true);
      const response = await fetch(`${API_BASE_URL}/clear-data`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ confirm: true })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || 'Failed to clear data');
      }

      const data = await response.json();
      if (data.status === 'success') {
        // Refresh alerts (will be empty now)
        setAlerts([]);
        setShowClearConfirm(false);
        // Trigger page refresh to clear map and analytics
        window.location.reload();
      }
    } catch (err) {
      console.error('Error clearing data:', err);
      alert(`Error clearing data: ${err.message}`);
      setShowClearConfirm(false);
    } finally {
      setClearing(false);
    }
  };

  // Don't render anything if loading, error, or no alerts
  // Only show the panel when there are actual serious alerts
  if (loading || error || alerts.length === 0) {
    return null;
  }

  return (
    <div className="card" data-alerts-panel>
      <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2>🚨 Serious Alerts</h2>
          <p className="subtitle">
            {alerts.length} high-credibility disaster{alerts.length > 1 ? 's' : ''} detected
          </p>
        </div>
        <button
          onClick={handleClearData}
          disabled={clearing}
          style={{
            padding: '8px 16px',
            background: showClearConfirm 
              ? 'linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)'
              : 'rgba(239, 68, 68, 0.1)',
            border: `2px solid ${showClearConfirm ? '#dc2626' : 'rgba(239, 68, 68, 0.3)'}`,
            borderRadius: '8px',
            color: showClearConfirm ? 'white' : '#ef4444',
            fontSize: '0.85rem',
            fontWeight: 600,
            cursor: clearing ? 'not-allowed' : 'pointer',
            transition: 'all 0.3s ease',
            whiteSpace: 'nowrap',
            opacity: clearing ? 0.6 : 1
          }}
          onMouseEnter={(e) => {
            if (!clearing && !showClearConfirm) {
              e.target.style.background = 'rgba(239, 68, 68, 0.2)';
              e.target.style.borderColor = 'rgba(239, 68, 68, 0.5)';
            }
          }}
          onMouseLeave={(e) => {
            if (!clearing && !showClearConfirm) {
              e.target.style.background = 'rgba(239, 68, 68, 0.1)';
              e.target.style.borderColor = 'rgba(239, 68, 68, 0.3)';
            }
          }}
        >
          {clearing ? (
            <>
              <span className="spinner" style={{ marginRight: '6px' }}></span>
              Clearing...
            </>
          ) : showClearConfirm ? (
            '⚠️ Confirm Clear All Data'
          ) : (
            '🗑️ Clear All Data'
          )}
        </button>
      </div>
      
      {showClearConfirm && !clearing && (
        <div style={{
          marginBottom: '16px',
          padding: '12px',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          borderRadius: '8px',
          fontSize: '0.9rem',
          color: '#fca5a5'
        }}>
          ⚠️ This will permanently delete all tweets, clusters, and alerts. This action cannot be undone.
          <div style={{ marginTop: '8px', display: 'flex', gap: '8px' }}>
            <button
              onClick={handleClearData}
              style={{
                padding: '6px 12px',
                background: '#dc2626',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              Yes, Clear All
            </button>
            <button
              onClick={() => setShowClearConfirm(false)}
              style={{
                padding: '6px 12px',
                background: 'rgba(255, 255, 255, 0.1)',
                color: '#cbd5e1',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                borderRadius: '6px',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {alerts.map((alert) => (
          <div
            key={alert.id}
            style={{
              padding: '16px',
              background: `linear-gradient(135deg, ${getAlertColor(alert.alert_level)}15 0%, ${getAlertColor(alert.alert_level)}05 100%)`,
              border: `2px solid ${getAlertColor(alert.alert_level)}40`,
              borderRadius: '12px',
              animation: 'scaleIn 0.4s ease',
              position: 'relative',
              overflow: 'hidden'
            }}
          >
            {/* Alert Header */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
              <span style={{ fontSize: '1.5rem' }}>{getAlertIcon(alert.alert_level)}</span>
              <div style={{ flex: 1 }}>
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '8px',
                  marginBottom: '4px'
                }}>
                  <strong style={{ 
                    fontSize: '1.1rem',
                    color: getAlertColor(alert.alert_level)
                  }}>
                    {alert.category}
                  </strong>
                  <span style={{
                    padding: '4px 10px',
                    background: getAlertColor(alert.alert_level),
                    color: 'white',
                    borderRadius: '6px',
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    textTransform: 'uppercase'
                  }}>
                    {alert.alert_level}
                  </span>
                </div>
                <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
                  {alert.severity} Severity • {alert.tweet_count} report{alert.tweet_count > 1 ? 's' : ''}
                </div>
              </div>
            </div>

            {/* Credibility Score */}
            <div style={{ marginBottom: '12px' }}>
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '6px'
              }}>
                <span style={{ fontSize: '0.85rem', color: '#94a3b8', fontWeight: 500 }}>
                  Credibility Score
                </span>
                <span style={{ 
                  fontSize: '1rem', 
                  fontWeight: 700,
                  color: alert.credibility_score >= 0.8 ? '#10b981' : '#f59e0b'
                }}>
                  {(alert.credibility_score * 100).toFixed(0)}%
                </span>
              </div>
              <div style={{
                width: '100%',
                height: '8px',
                background: 'rgba(0, 0, 0, 0.2)',
                borderRadius: '4px',
                overflow: 'hidden'
              }}>
                <div style={{
                  width: `${alert.credibility_score * 100}%`,
                  height: '100%',
                  background: `linear-gradient(90deg, ${getAlertColor(alert.alert_level)} 0%, ${getAlertColor(alert.alert_level)}cc 100%)`,
                  borderRadius: '4px',
                  transition: 'width 0.5s ease'
                }}></div>
              </div>
            </div>

            {/* Location */}
            {alert.location && alert.location.lat && alert.location.lon && (
              <div style={{
                padding: '8px 12px',
                background: 'rgba(0, 0, 0, 0.1)',
                borderRadius: '6px',
                fontSize: '0.85rem',
                color: '#cbd5e1',
                fontFamily: 'monospace',
                marginBottom: '12px'
              }}>
                📍 {alert.location.lat.toFixed(4)}, {alert.location.lon.toFixed(4)}
              </div>
            )}

            {/* Sample Tweets */}
            {alert.tweets && alert.tweets.length > 0 && (
              <div>
                <div style={{ 
                  fontSize: '0.85rem', 
                  color: '#94a3b8',
                  marginBottom: '8px',
                  fontWeight: 500
                }}>
                  Recent Reports ({alert.tweets.length}):
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {alert.tweets.slice(0, 3).map((tweet, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: '8px',
                        background: 'rgba(0, 0, 0, 0.1)',
                        borderRadius: '6px',
                        fontSize: '0.85rem',
                        color: '#cbd5e1',
                        lineHeight: '1.4',
                        borderLeft: `3px solid ${getAlertColor(alert.alert_level)}`
                      }}
                    >
                      "{tweet.text?.substring(0, 100)}{tweet.text?.length > 100 ? '...' : ''}"
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default AlertsPanel;

