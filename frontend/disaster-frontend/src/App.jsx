import React, { useState, useCallback, useEffect } from 'react';
import './App.css';
import DisasterForm from './components/DisasterForm';
import ResultPanel from './components/ResultPanel';
import DisasterMap from './components/DisasterMap';
import AnalyticsPanel from './components/AnalyticsPanel';
import AlertsPanel from './components/AlertsPanel';
import ErrorBoundary from './components/ErrorBoundary';
import { simulationTweets, simulationInfo } from './data/simulationTweets';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

function App() {
  const [currentResult, setCurrentResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [simulating, setSimulating] = useState(false);
  const [simulationProgress, setSimulationProgress] = useState({ current: 0, total: 0 });
  const [simulationText, setSimulationText] = useState(null);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [clearing, setClearing] = useState(false);

  const handleAnalyze = useCallback(async (text) => {
    if (!text || !text.trim()) {
      setError('Please enter a tweet text.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE_URL}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text.trim() }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(
          errorData.message || errorData.error || `Server error: ${res.status}`
        );
      }

      const data = await res.json();

      if (data.status === 'error') {
        throw new Error(data.message || data.error || 'An error occurred');
      }

      setCurrentResult(data);
      setHistory((prev) => [data, ...prev.slice(0, 49)]); // keep last 50
    } catch (err) {
      console.error('Analysis error:', err);
      const errorMessage =
        err.message ||
        'Failed to connect to backend. Make sure the API is running on http://localhost:5000';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const handleClearAllData = useCallback(async () => {
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
        // Clear local state
        setCurrentResult(null);
        setHistory([]);
        setShowClearConfirm(false);
        // Show success message
        alert(`✅ All data cleared successfully!\n\nDeleted:\n- ${data.deleted?.tweets_deleted || 0} tweets\n- ${data.deleted?.clusters_deleted || 0} clusters`);
        // Refresh page to reset everything
        window.location.reload();
      }
    } catch (err) {
      console.error('Error clearing data:', err);
      setError(`Error clearing data: ${err.message}`);
      setShowClearConfirm(false);
    } finally {
      setClearing(false);
    }
  }, [showClearConfirm]);

  // Load historical tweets from database on mount
  useEffect(() => {
    const loadHistory = async () => {
      try {
        setLoadingHistory(true);
        const response = await fetch(`${API_BASE_URL}/tweets?limit=100&disaster_only=false`);
        if (response.ok) {
          const data = await response.json();
          if (data.status === 'success' && data.tweets && data.tweets.length > 0) {
            // Convert database format to frontend format
            const formattedTweets = data.tweets.map(tweet => ({
              ...tweet,
              // Ensure all required fields are present
              confidence: tweet.confidence || 0.0,
              confidence_percentage: tweet.confidence_percentage || (tweet.confidence * 100) || 0.0,
            }));
            
            setHistory(formattedTweets);
            // Set the most recent tweet as current result
            if (formattedTweets.length > 0) {
              setCurrentResult(formattedTweets[0]);
            }
            console.log(`Loaded ${formattedTweets.length} tweets from database`);
          }
        }
      } catch (err) {
        console.error('Error loading history:', err);
        // Don't show error to user, just continue with empty state
      } finally {
        setLoadingHistory(false);
      }
    };

    loadHistory();
  }, []); // Only run once on mount

  const runSimulation = useCallback(async () => {
    if (simulating || loading) return;
    
    setSimulating(true);
    setError(null);
    setSimulationProgress({ current: 0, total: simulationTweets.length });
    
    try {
      setCurrentResult(null); // Clear current result for fresh start
      
      // Process tweets one by one with smooth transitions
      for (let i = 0; i < simulationTweets.length; i++) {
        const tweet = simulationTweets[i];
        
        // Update progress smoothly
        setSimulationProgress({ current: i + 1, total: simulationTweets.length });
        
        // Smoothly set the text in the form (for visual feedback)
        setSimulationText(tweet);
        
        // Wait for text to appear smoothly in UI (fade in effect)
        await new Promise(resolve => setTimeout(resolve, 600));
        
        // Analyze the tweet
        await handleAnalyze(tweet);
        
        // Wait for result to appear before moving to next (smooth transition)
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Smooth delay between requests (varies slightly for natural feel)
        if (i < simulationTweets.length - 1) {
          const delay = 1200 + Math.random() * 400; // 1.2-1.6 seconds (more natural)
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
      
      // Clear simulation text smoothly
      setSimulationText(null);
      
      // Wait for clustering to process and update
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Check for alerts multiple times (clustering may take a moment)
      let alertsFound = false;
      for (let check = 0; check < 3; check++) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        try {
          const alertsResponse = await fetch(`${API_BASE_URL}/alerts?min_credibility=0.7`);
          if (alertsResponse.ok) {
            const alertsData = await alertsResponse.json();
            if (alertsData.status === 'success' && alertsData.alerts && alertsData.alerts.length > 0) {
              alertsFound = true;
              
              // Show prominent alert notification
              const alertNotification = document.createElement('div');
              alertNotification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
                color: white;
                padding: 24px 28px;
                border-radius: 14px;
                box-shadow: 0 10px 40px rgba(220, 38, 38, 0.6);
                z-index: 10001;
                max-width: 450px;
                animation: slideInRight 0.6s ease;
                font-family: system-ui, sans-serif;
                line-height: 1.6;
                border: 3px solid rgba(255, 255, 255, 0.3);
              `;
              
              const topAlert = alertsData.alerts[0];
              alertNotification.innerHTML = `
                <div style="font-size: 1.4rem; font-weight: 800; margin-bottom: 12px; display: flex; align-items: center; gap: 10px;">
                  <span style="font-size: 2rem; animation: pulse 1.5s infinite;">🚨</span>
                  <span>CRITICAL ALERT DETECTED!</span>
                </div>
                <div style="font-size: 1rem; opacity: 0.95; margin-bottom: 10px; font-weight: 600;">
                  <strong>${alertsData.alerts.length} serious alert${alertsData.alerts.length > 1 ? 's' : ''}</strong> generated from simulation
                </div>
                ${topAlert ? `
                <div style="font-size: 0.9rem; opacity: 0.9; padding: 10px; background: rgba(0,0,0,0.2); border-radius: 8px; margin-bottom: 10px;">
                  <div><strong>📍 Location:</strong> ${topAlert.location ? `${topAlert.location.lat?.toFixed(4)}, ${topAlert.location.lon?.toFixed(4)}` : 'Unknown'}</div>
                  <div><strong>⚠️ Type:</strong> ${topAlert.category || 'Disaster'}</div>
                  <div><strong>⭐ Credibility:</strong> ${(topAlert.credibility_score * 100).toFixed(0)}%</div>
                  <div><strong>📊 Reports:</strong> ${topAlert.tweet_count} tweets</div>
                </div>
                ` : ''}
                <div style="font-size: 0.85rem; opacity: 0.9; padding-top: 10px; border-top: 2px solid rgba(255,255,255,0.3); font-weight: 600;">
                  👉 Check the Alerts Panel (top right) for full details
                </div>
              `;
              document.body.appendChild(alertNotification);
              
              // Pulse the notification
              setTimeout(() => {
                alertNotification.style.animation = 'pulse 1s ease 2';
              }, 600);
              
              // Auto-remove after 10 seconds
              setTimeout(() => {
                alertNotification.style.animation = 'fadeOut 0.6s ease';
                setTimeout(() => alertNotification.remove(), 600);
              }, 10000);
              
              // Highlight AlertsPanel with animation (wait a bit for it to render)
              setTimeout(() => {
                // Try multiple times since panel might take a moment to appear
                let attempts = 0;
                const tryHighlight = () => {
                  const alertsPanel = document.querySelector('[data-alerts-panel]');
                  if (alertsPanel) {
                    alertsPanel.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    alertsPanel.style.animation = 'pulse 1s ease 4';
                    alertsPanel.style.border = '3px solid rgba(220, 38, 38, 0.8)';
                    alertsPanel.style.boxShadow = '0 0 30px rgba(220, 38, 38, 0.6)';
                    alertsPanel.style.transform = 'scale(1.02)';
                    
                    setTimeout(() => {
                      alertsPanel.style.animation = '';
                      alertsPanel.style.transform = '';
                    }, 4000);
                    
                    setTimeout(() => {
                      alertsPanel.style.border = '';
                      alertsPanel.style.boxShadow = '';
                    }, 5000);
                  } else if (attempts < 5) {
                    // Retry if panel not found yet (might still be rendering)
                    attempts++;
                    setTimeout(tryHighlight, 300);
                  }
                };
                tryHighlight();
              }, 500);
              
              break; // Found alerts, no need to check again
            }
          }
        } catch (err) {
          console.error('Error checking alerts:', err);
        }
      }
      
      // If no alerts found, mention it in success message
      if (!alertsFound) {
        console.log('No alerts detected after simulation - clustering may need more time');
      }
      
      // Show elegant success notification (instead of alert)
      const notification = document.createElement('div');
      notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 20px 24px;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(16, 185, 129, 0.4);
        z-index: 10000;
        max-width: 420px;
        animation: slideInRight 0.5s ease;
        font-family: system-ui, sans-serif;
        line-height: 1.6;
      `;
      notification.innerHTML = `
        <div style="font-size: 1.3rem; font-weight: 700; margin-bottom: 10px; display: flex; align-items: center; gap: 8px;">
          <span>✅</span>
          <span>Simulation Complete!</span>
        </div>
        <div style="font-size: 0.95rem; opacity: 0.95; margin-bottom: 8px;">
          <strong>${simulationTweets.length} tweets</strong> analyzed successfully
        </div>
        <div style="font-size: 0.85rem; opacity: 0.9; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.2);">
          📍 Check map and alerts panel for clusters and alerts
        </div>
      `;
      document.body.appendChild(notification);
      
      // Auto-remove notification after 6 seconds with fade out
      setTimeout(() => {
        notification.style.animation = 'fadeOut 0.5s ease';
        setTimeout(() => notification.remove(), 500);
      }, 6000);
      
    } catch (err) {
      console.error('Simulation error:', err);
      setError(`Simulation error: ${err.message}`);
      setSimulationText(null);
    } finally {
      setSimulating(false);
      setSimulationProgress({ current: 0, total: 0 });
    }
  }, [simulating, loading, handleAnalyze]);

  return (
    <ErrorBoundary>
      <div className="app-root">
        <header>
          <div className="header-content">
            <h1>🚨 AI Disaster Intelligence System</h1>
            <p className="header-subtitle">
              Advanced NLP-powered disaster detection and geotagging platform
            </p>
            <div className="header-badges">
              <span className="header-badge">🤖 AI-Powered</span>
              <span className="header-badge">📍 Real-time Geotagging</span>
              <span className="header-badge">📊 Advanced Analytics</span>
              <span className="header-badge">⚡ Production-Ready</span>
            </div>
            
            {/* Flush/Clear Data Button */}
            <div style={{ marginTop: '16px' }}>
              <button
                onClick={handleClearAllData}
                disabled={clearing || loadingHistory}
                style={{
                  padding: '10px 20px',
                  background: showClearConfirm 
                    ? 'linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)'
                    : 'rgba(239, 68, 68, 0.1)',
                  border: `2px solid ${showClearConfirm ? '#dc2626' : 'rgba(239, 68, 68, 0.3)'}`,
                  borderRadius: '10px',
                  color: showClearConfirm ? 'white' : '#ef4444',
                  fontSize: '0.9rem',
                  fontWeight: 600,
                  cursor: (clearing || loadingHistory) ? 'not-allowed' : 'pointer',
                  transition: 'all 0.3s ease',
                  whiteSpace: 'nowrap',
                  opacity: (clearing || loadingHistory) ? 0.6 : 1,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  margin: '0 auto'
                }}
                onMouseEnter={(e) => {
                  if (!clearing && !loadingHistory && !showClearConfirm) {
                    e.target.style.background = 'rgba(239, 68, 68, 0.2)';
                    e.target.style.borderColor = 'rgba(239, 68, 68, 0.5)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!clearing && !loadingHistory && !showClearConfirm) {
                    e.target.style.background = 'rgba(239, 68, 68, 0.1)';
                    e.target.style.borderColor = 'rgba(239, 68, 68, 0.3)';
                  }
                }}
              >
                {clearing ? (
                  <>
                    <span className="spinner" style={{ width: '14px', height: '14px' }}></span>
                    <span>Clearing...</span>
                  </>
                ) : showClearConfirm ? (
                  <>
                    <span>⚠️</span>
                    <span>Confirm Delete All Data</span>
                  </>
                ) : (
                  <>
                    <span>🗑️</span>
                    <span>Flush All Data</span>
                  </>
                )}
              </button>
              
              {showClearConfirm && !clearing && (
                <div style={{
                  marginTop: '12px',
                  padding: '14px',
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '2px solid rgba(239, 68, 68, 0.4)',
                  borderRadius: '10px',
                  fontSize: '0.9rem',
                  color: '#fca5a5',
                  maxWidth: '500px',
                  margin: '12px auto 0',
                  textAlign: 'center'
                }}>
                  <div style={{ marginBottom: '10px', fontWeight: 600, fontSize: '1rem' }}>
                    ⚠️ Warning: This will permanently delete ALL data!
                  </div>
                  <div style={{ marginBottom: '12px', lineHeight: '1.6' }}>
                    This action will delete:
                    <ul style={{ textAlign: 'left', display: 'inline-block', marginTop: '8px', marginBottom: '8px' }}>
                      <li>All analyzed tweets</li>
                      <li>All clusters</li>
                      <li>All alerts</li>
                      <li>All analytics data</li>
                    </ul>
                    <strong>This action cannot be undone!</strong>
                  </div>
                  <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
                    <button
                      onClick={handleClearAllData}
                      style={{
                        padding: '8px 20px',
                        background: '#dc2626',
                        color: 'white',
                        border: 'none',
                        borderRadius: '8px',
                        fontSize: '0.9rem',
                        fontWeight: 700,
                        cursor: 'pointer',
                        transition: 'all 0.2s ease'
                      }}
                      onMouseEnter={(e) => {
                        e.target.style.background = '#b91c1c';
                        e.target.style.transform = 'scale(1.05)';
                      }}
                      onMouseLeave={(e) => {
                        e.target.style.background = '#dc2626';
                        e.target.style.transform = 'scale(1)';
                      }}
                    >
                      Yes, Delete Everything
                    </button>
                    <button
                      onClick={() => setShowClearConfirm(false)}
                      style={{
                        padding: '8px 20px',
                        background: 'rgba(255, 255, 255, 0.1)',
                        color: '#cbd5e1',
                        border: '1px solid rgba(255, 255, 255, 0.2)',
                        borderRadius: '8px',
                        fontSize: '0.9rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        transition: 'all 0.2s ease'
                      }}
                      onMouseEnter={(e) => {
                        e.target.style.background = 'rgba(255, 255, 255, 0.2)';
                      }}
                      onMouseLeave={(e) => {
                        e.target.style.background = 'rgba(255, 255, 255, 0.1)';
                      }}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>
            
            {/* Simulation Button */}
            <div style={{ marginTop: '20px' }}>
              <button
                onClick={runSimulation}
                disabled={simulating || loading}
                style={{
                  padding: '12px 24px',
                  background: simulating 
                    ? 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)'
                    : 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                  border: 'none',
                  borderRadius: '12px',
                  color: 'white',
                  fontSize: '1rem',
                  fontWeight: 600,
                  cursor: (simulating || loading) ? 'not-allowed' : 'pointer',
                  transition: 'all 0.3s ease',
                  boxShadow: '0 4px 15px rgba(16, 185, 129, 0.3)',
                  opacity: (simulating || loading) ? 0.7 : 1,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  margin: '0 auto'
                }}
                onMouseEnter={(e) => {
                  if (!simulating && !loading) {
                    e.target.style.transform = 'translateY(-2px)';
                    e.target.style.boxShadow = '0 6px 20px rgba(16, 185, 129, 0.4)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!simulating && !loading) {
                    e.target.style.transform = 'translateY(0)';
                    e.target.style.boxShadow = '0 4px 15px rgba(16, 185, 129, 0.3)';
                  }
                }}
              >
                {simulating ? (
                  <>
                    <span className="spinner"></span>
                    <span>Running Simulation... ({simulationProgress.current}/{simulationProgress.total})</span>
                  </>
                ) : (
                  <>
                    <span>🎬</span>
                    <span>Run Simulation: {simulationInfo.location}</span>
                  </>
                )}
              </button>
              {simulating && (
                <div style={{
                  marginTop: '16px',
                  padding: '16px',
                  background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(5, 150, 105, 0.1) 100%)',
                  border: '2px solid rgba(16, 185, 129, 0.3)',
                  borderRadius: '12px',
                  fontSize: '0.9rem',
                  color: '#10b981',
                  maxWidth: '550px',
                  margin: '16px auto 0',
                  animation: 'fadeIn 0.5s ease',
                  boxShadow: '0 4px 20px rgba(16, 185, 129, 0.2)'
                }}>
                  <div style={{ 
                    marginBottom: '12px', 
                    fontWeight: 700,
                    fontSize: '1.05rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}>
                    <span style={{ 
                      animation: 'pulse 2s ease-in-out infinite',
                      fontSize: '1.2rem'
                    }}>🎬</span>
                    <span>Simulating: {simulationInfo.location}</span>
                  </div>
                  
                  <div style={{ 
                    marginBottom: '12px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}>
                    <span style={{ fontWeight: 500 }}>
                      Analyzing tweet {simulationProgress.current} of {simulationProgress.total}...
                    </span>
                    <span style={{ 
                      fontWeight: 700,
                      fontSize: '1.1rem',
                      color: '#059669'
                    }}>
                      {Math.round((simulationProgress.current / simulationProgress.total) * 100)}%
                    </span>
                  </div>
                  
                  <div style={{
                    width: '100%',
                    height: '12px',
                    background: 'rgba(0, 0, 0, 0.2)',
                    borderRadius: '6px',
                    overflow: 'hidden',
                    marginBottom: '12px',
                    boxShadow: 'inset 0 2px 4px rgba(0, 0, 0, 0.1)'
                  }}>
                    <div style={{
                      width: `${(simulationProgress.current / simulationProgress.total) * 100}%`,
                      height: '100%',
                      background: 'linear-gradient(90deg, #10b981 0%, #059669 50%, #047857 100%)',
                      borderRadius: '6px',
                      transition: 'width 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
                      boxShadow: '0 2px 8px rgba(16, 185, 129, 0.4)',
                      position: 'relative',
                      overflow: 'hidden'
                    }}>
                      <div style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        background: 'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent)',
                        animation: 'shimmer 2s infinite'
                      }}></div>
                    </div>
                  </div>
                  
                  <div style={{ 
                    fontSize: '0.85rem', 
                    opacity: 0.9,
                    lineHeight: '1.5',
                    padding: '8px',
                    background: 'rgba(0, 0, 0, 0.1)',
                    borderRadius: '6px'
                  }}>
                    <span style={{ fontWeight: 600 }}>Expected Results:</span> Cluster near {simulationInfo.location} • {simulationInfo.disasterType} alert • High credibility score
                  </div>
                </div>
              )}
            </div>
          </div>
        </header>

        {error && (
          <div className="error-banner" onClick={clearError}>
            <span className="error-icon">⚠️</span>
            <span className="error-message">{error}</span>
            <button className="error-close" onClick={clearError}>×</button>
          </div>
        )}

        <main className="layout">
          <section className="left">
            <DisasterForm 
              onAnalyze={handleAnalyze} 
              loading={loading || simulating}
              simulationText={simulationText}
            />
            <ResultPanel result={currentResult} loading={loading || simulating} />
          </section>
          <section className="right">
            <div id="alerts-panel-container">
              <AlertsPanel />
            </div>
            <DisasterMap
              results={
                currentResult ? [currentResult, ...history] : history
              }
              loading={loadingHistory}
            />
            <AnalyticsPanel results={history} loading={loadingHistory} />
          </section>
        </main>

        <footer style={{
          marginTop: '48px',
          paddingTop: '32px',
          borderTop: '1px solid rgba(99, 102, 241, 0.2)',
          textAlign: 'center',
          color: 'var(--text-tertiary)',
          fontSize: '0.9rem'
        }}>
          <p style={{ marginBottom: '8px' }}>
            🚨 AI Disaster Intelligence System
          </p>
          <p style={{ fontSize: '0.85rem', opacity: 0.7 }}>
            Advanced NLP-powered disaster detection with real-time geotagging
          </p>
        </footer>
      </div>
    </ErrorBoundary>
  );
}

export default App;

