import React, { useState, useRef, useEffect } from 'react';
import SkeletonLoader from './SkeletonLoader';

function DisasterForm({ onAnalyze, loading, simulationText, onSimulationComplete }) {
  const [text, setText] = useState('');
  const [charCount, setCharCount] = useState(0);
  const textareaRef = useRef(null);
  
  // Handle simulation text updates with smooth transition
  useEffect(() => {
    if (simulationText !== null && simulationText !== text) {
      // Smooth fade transition
      if (text && textareaRef.current) {
        textareaRef.current.style.setProperty('opacity', '0.4');
        textareaRef.current.style.setProperty('transition', 'opacity 0.3s ease');
      }
      
      // Set new text after brief delay for smooth transition
      setTimeout(() => {
        setText(simulationText);
        if (textareaRef.current) {
          textareaRef.current.style.setProperty('opacity', '1');
          textareaRef.current.style.setProperty('transition', 'opacity 0.5s ease');
          // Smooth scroll to textarea for visibility
          setTimeout(() => {
            textareaRef.current?.scrollIntoView({ 
              behavior: 'smooth', 
              block: 'center' 
            });
          }, 100);
        }
      }, text ? 250 : 0);
    }
  }, [simulationText, text, loading]);

  useEffect(() => {
    setCharCount(text.length);
  }, [text]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!text.trim() || loading) {
      return;
    }
    onAnalyze(text.trim());
  };

  const handleKeyDown = (e) => {
    // Allow Ctrl+Enter or Cmd+Enter to submit
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      handleSubmit(e);
    }
  };

  const exampleTweets = [
    'Massive flood in Phagwara, Punjab. Roads are blocked! Emergency services are responding.',
    'Fire broke out in Mumbai building, 20 injured. Firefighters on scene.',
    'Earthquake tremors felt in Delhi, magnitude 5.2. Buildings shaking.',
    'Hurricane approaching Florida coast. Evacuation orders issued.',
  ];

  const handleExampleClick = (example) => {
    setText(example);
    textareaRef.current?.focus();
  };

  return (
    <div className="card form-card">
      <div className="card-header">
        <h2>🔍 Tweet Analysis</h2>
        <p className="subtitle">Enter a tweet to analyze for disaster classification</p>
      </div>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="tweet-input" className="form-label">
            Tweet Text
            {charCount > 0 && (
              <span style={{ 
                marginLeft: '8px', 
                fontSize: '0.85rem', 
                color: charCount > 280 ? '#ef4444' : '#94a3b8',
                fontWeight: 'normal'
              }}>
                ({charCount}/280)
              </span>
            )}
          </label>
          <textarea
            ref={textareaRef}
            id="tweet-input"
            rows={5}
            placeholder='Example: "Massive flood in Phagwara, Punjab. Roads are blocked! Emergency services are responding."'
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            className="tweet-input"
            disabled={loading}
            maxLength={500}
          />
          <div className="input-hint">
            💡 Tip: Include location names or coordinates for better geotagging results
            <br />
            <span style={{ fontSize: '0.8rem', opacity: 0.7 }}>
              Press Ctrl+Enter (or Cmd+Enter on Mac) to submit
            </span>
          </div>
        </div>

        {/* Example Tweets */}
        {!text && (
          <div style={{ 
            marginBottom: '16px', 
            padding: '12px', 
            background: 'rgba(99, 102, 241, 0.05)',
            borderRadius: '8px',
            border: '1px solid rgba(99, 102, 241, 0.1)'
          }}>
            <div style={{ 
              fontSize: '0.85rem', 
              color: '#94a3b8', 
              marginBottom: '8px',
              fontWeight: 500
            }}>
              📝 Quick Examples:
            </div>
            <div style={{ 
              display: 'flex', 
              flexWrap: 'wrap', 
              gap: '6px' 
            }}>
              {exampleTweets.slice(0, 2).map((example, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleExampleClick(example)}
                  style={{
                    padding: '6px 12px',
                    fontSize: '0.75rem',
                    background: 'rgba(99, 102, 241, 0.1)',
                    border: '1px solid rgba(99, 102, 241, 0.2)',
                    borderRadius: '6px',
                    color: '#a5b4fc',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    maxWidth: '200px'
                  }}
                  onMouseEnter={(e) => {
                    e.target.style.background = 'rgba(99, 102, 241, 0.2)';
                    e.target.style.transform = 'translateY(-1px)';
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.background = 'rgba(99, 102, 241, 0.1)';
                    e.target.style.transform = 'translateY(0)';
                  }}
                >
                  {example.split('.')[0]}...
                </button>
              ))}
            </div>
          </div>
        )}

        <button
          type="submit"
          disabled={loading || !text.trim()}
          className="analyze-button"
        >
          {loading ? (
            <>
              <span className="spinner"></span>
              <span>Analyzing...</span>
            </>
          ) : (
            <>
              <span>🚀</span>
              <span>Analyze Tweet</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
}

export default DisasterForm;




