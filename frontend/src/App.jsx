import React, { useMemo, useState } from "react";
import "./App.css";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

function App() {
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const examples = [
    "Massive flood near Yamuna in Delhi, roads are blocked.",
    "5.4 earthquake felt in Kathmandu, buildings shaking.",
    "Fire reported at warehouse in Mumbai industrial area.",
  ];

  const confidencePct = useMemo(() => {
    if (!result) return 0;
    const raw = result.confidence_percentage ?? (result.confidence || 0) * 100;
    return Number(raw).toFixed(1);
  }, [result]);

  const mapUrl = useMemo(() => {
    if (
      !result ||
      result.disaster_label !== 1 ||
      result.lat == null ||
      result.lon == null
    ) {
      return null;
    }

    const lat = Number(result.lat);
    const lon = Number(result.lon);
    if (Number.isNaN(lat) || Number.isNaN(lon)) {
      return null;
    }

    const delta = 0.04;
    const left = lon - delta;
    const right = lon + delta;
    const top = lat + delta;
    const bottom = lat - delta;
    return `https://www.openstreetmap.org/export/embed.html?bbox=${left},${bottom},${right},${top}&layer=mapnik&marker=${lat},${lon}`;
  }, [result]);

  const onSubmit = async (event) => {
    event.preventDefault();
    const payload = text.trim();

    if (!payload) {
      setError("Please enter tweet text.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_BASE_URL}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: payload }),
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok || data.status === "error") {
        throw new Error(data.message || data.error || "Prediction failed.");
      }

      setResult(data);
      setHistory((prev) => [data, ...prev].slice(0, 8));
    } catch (err) {
      setError(
        err.message ||
          "Unable to reach backend. Check API URL and backend server status.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <main className="shell">
        <header className="hero">
          <h1>
            Disaster Tweet Classification <span className="amp">&amp;</span>{" "}
            Geotagging
          </h1>
          <p>
            Paste a tweet to detect disaster risk, severity, and pinpoint the
            location on a map.
          </p>
        </header>

        <section className="panel">
          <h2>Analyze Tweet</h2>
          <div className="examples">
            {examples.map((item) => (
              <button
                key={item}
                type="button"
                className="example-chip"
                onClick={() => setText(item)}
                disabled={loading}
              >
                {item}
              </button>
            ))}
          </div>
          <form onSubmit={onSubmit} className="form">
            <label htmlFor="tweet">Tweet text</label>
            <textarea
              id="tweet"
              className="textarea"
              rows={5}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Example: Flood in Delhi near Yamuna river, roads blocked."
              disabled={loading}
            />
            <button type="submit" className="button" disabled={loading}>
              {loading ? "Analyzing..." : "Analyze"}
            </button>
          </form>
          {error && <p className="error">{error}</p>}
        </section>

        <section className="panel">
          <h2>Result</h2>
          {!result && <p className="muted">No prediction yet.</p>}

          {result && (
            <>
              <div className="result-verdict">
                <span
                  className={`verdict-badge ${result.disaster_label ? "verdict-disaster" : "verdict-safe"}`}
                >
                  {result.disaster_label ? "⚠ Disaster" : "✓ Safe"}
                </span>
                <span className="verdict-conf">
                  {confidencePct}% confidence
                </span>
              </div>

              <div className="result-rows">
                <div className="row">
                  <span className="row-label">Category</span>
                  <span className="row-value">{result.category || "—"}</span>
                </div>
                <div className="row">
                  <span className="row-label">Severity</span>
                  <span className="row-value">{result.severity || "—"}</span>
                </div>
                <div className="row">
                  <span className="row-label">Risk Level</span>
                  <span className="row-value">{result.risk_level || "—"}</span>
                </div>
                <div className="row">
                  <span className="row-label">Location</span>
                  <span className="row-value">
                    {result.location ||
                      result.location_mention ||
                      "Not detected"}
                  </span>
                </div>
                {result.lat != null && result.lon != null && (
                  <div className="row">
                    <span className="row-label">Coordinates</span>
                    <span className="row-value">
                      {Number(result.lat).toFixed(4)},{" "}
                      {Number(result.lon).toFixed(4)}
                    </span>
                  </div>
                )}
                <div className="row">
                  <span className="row-label">Model</span>
                  <span className="row-value">
                    {result.model_info?.model_name || "—"}
                  </span>
                </div>
                <div className="row">
                  <span className="row-label">Processing</span>
                  <span className="row-value">
                    {result.processing_time_ms
                      ? `${Number(result.processing_time_ms).toFixed(1)} ms`
                      : "—"}
                  </span>
                </div>
              </div>
            </>
          )}

          {mapUrl && (
            <div className="map-block">
              <p className="map-title">Location Preview</p>
              <iframe
                title="location-map-preview"
                className="map-frame"
                src={mapUrl}
                loading="lazy"
              />
              <a
                className="map-link"
                href={`https://www.openstreetmap.org/?mlat=${Number(result.lat)}&mlon=${Number(result.lon)}#map=12/${Number(result.lat)}/${Number(result.lon)}`}
                target="_blank"
                rel="noreferrer"
              >
                Open in OpenStreetMap
              </a>
            </div>
          )}
        </section>

        <section className="panel">
          <h2>Recent Predictions</h2>
          {history.length === 0 && (
            <p className="muted">No recent predictions.</p>
          )}
          {history.length > 0 && (
            <ul className="history-list">
              {history.map((item, index) => (
                <li key={`${item.tweet}-${index}`}>
                  <button
                    type="button"
                    className="history-item"
                    onClick={() => setResult(item)}
                  >
                    <span className="history-text">{item.tweet}</span>
                    <span
                      className={`badge ${
                        item.disaster_label ? "badge-danger" : "badge-safe"
                      }`}
                    >
                      {item.disaster_label ? "Disaster" : "Safe"}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      </main>

      <footer className="footer">Made with ❤️ by Aakash</footer>
    </div>
  );
}

export default App;
