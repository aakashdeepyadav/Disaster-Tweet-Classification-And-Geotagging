import React, { useEffect, useMemo, useState, useRef } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Circle,
  useMap,
  ZoomControl,
} from "react-leaflet";
import L from "leaflet";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

// Component to handle map zoom and centering with smooth transitions
function MapController({
  markers,
  previousLocation,
  onZoomOut,
  onZoomIn,
  enableInteraction = true,
}) {
  const map = useMap();
  const isTransitioningRef = useRef(false);
  const lastMarkerRef = useRef(null);

  // If interactions are disabled, do not set zoom functions or perform fly/fit
  useEffect(() => {
    if (!enableInteraction) {
      if (onZoomOut) onZoomOut.current = null;
      return;
    }

    if (onZoomOut && map) {
      onZoomOut.current = () => {
        if (markers.length > 0) {
          // If there are markers, zoom out to show all locations
          if (markers.length === 1) {
            // Single marker: zoom out but keep it centered
            const marker = markers[0];
            if (marker.lat && marker.lon) {
              map.flyTo([marker.lat, marker.lon], 6, {
                animate: true,
                duration: 1.0,
                easeLinearity: 0.25,
              });
            }
          } else {
            // Multiple markers: fit bounds to show all
            const validMarkers = markers.filter((m) => m.lat && m.lon);
            if (validMarkers.length > 0) {
              const bounds = L.latLngBounds(
                validMarkers.map((m) => [m.lat, m.lon])
              );
              map.flyToBounds(bounds, {
                padding: [50, 50],
                maxZoom: 8,
                duration: 1.0,
                easeLinearity: 0.25,
              });
            }
          }
        } else {
          // No markers: zoom out to default view
          map.flyTo([22.9734, 78.6569], 4, {
            animate: true,
            duration: 1.0,
            easeLinearity: 0.25,
          });
        }
      };
    }
  }, [map, onZoomOut, markers, enableInteraction]);

  // Expose zoom in function to parent
  useEffect(() => {
    if (!enableInteraction) {
      if (onZoomIn) onZoomIn.current = null;
      return;
    }

    if (onZoomIn && map) {
      onZoomIn.current = () => {
        if (markers.length > 0) {
          // If there are markers, zoom in to the location(s) with maximum zoom
          if (markers.length === 1) {
            // Single marker: zoom in to maximum zoom level (19)
            const marker = markers[0];
            if (marker.lat && marker.lon) {
              map.flyTo([marker.lat, marker.lon], 19, {
                animate: true,
                duration: 1.0,
                easeLinearity: 0.25,
              });
            }
          } else {
            // Multiple markers: fit bounds with maximum zoom
            const validMarkers = markers.filter((m) => m.lat && m.lon);
            if (validMarkers.length > 0) {
              const bounds = L.latLngBounds(
                validMarkers.map((m) => [m.lat, m.lon])
              );
              map.flyToBounds(bounds, {
                padding: [50, 50],
                maxZoom: 19, // Maximum zoom level
                duration: 1.0,
                easeLinearity: 0.25,
              });
            }
          }
        }
      };
    }
  }, [map, onZoomIn, markers, enableInteraction]);

  useEffect(() => {
    if (!map || !enableInteraction) return;

    if (markers.length === 0) {
      // Default view if no markers
      map.setView([22.9734, 78.6569], 4, { animate: true, duration: 1.0 });
      return;
    }

    if (markers.length === 1) {
      // Single marker: always zoom in to the location
      const marker = markers[0];
      if (marker.lat && marker.lon) {
        const newLocation = [marker.lat, marker.lon];

        // Always zoom in to the location (smooth animation)
        map.flyTo(newLocation, 13, {
          animate: true,
          duration: 1.0,
          easeLinearity: 0.25,
        });
      }
    } else {
      // Multiple markers: fit bounds to show all
      const validMarkers = markers.filter((m) => m.lat && m.lon);
      if (validMarkers.length > 0) {
        const bounds = L.latLngBounds(validMarkers.map((m) => [m.lat, m.lon]));
        map.flyToBounds(bounds, {
          padding: [50, 50],
          maxZoom: 12,
          duration: 1.2,
          easeLinearity: 0.25,
        });
      }
    }
  }, [markers, map, previousLocation, enableInteraction]);

  return null;
}

function DisasterMap({ results, loading = false }) {
  const defaultCenter = [22.9734, 78.6569]; // India approx
  const [clusters, setClusters] = useState([]);
  const [showClusters, setShowClusters] = useState(true);
  const [previousLocation, setPreviousLocation] = useState(null);
  const zoomOutRef = useRef(null);
  const zoomInRef = useRef(null);

  // Fetch clusters
  useEffect(() => {
    const fetchClusters = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/clusters`);
        if (response.ok) {
          const data = await response.json();
          if (data.status === "success") {
            setClusters(data.clusters || []);
          }
        }
      } catch (err) {
        console.error("Error fetching clusters:", err);
      }
    };
    fetchClusters();
    const interval = setInterval(fetchClusters, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  // Ensure results is an array
  const resultsArray = useMemo(() => {
    return Array.isArray(results) ? results : results ? [results] : [];
  }, [results]);

  // Filter markers - ensure lat and lon are valid numbers
  const markers = useMemo(() => {
    return resultsArray
      .filter((r) => {
        if (!r) return false;
        const lat = r.lat;
        const lon = r.lon;
        const isValid =
          lat != null &&
          lon != null &&
          !isNaN(Number(lat)) &&
          !isNaN(Number(lon)) &&
          Number(lat) >= -90 &&
          Number(lat) <= 90 &&
          Number(lon) >= -180 &&
          Number(lon) <= 180;
        return isValid;
      })
      .map((r) => ({
        ...r,
        lat: Number(r.lat),
        lon: Number(r.lon),
      }));
  }, [resultsArray]);

  // Track previous location for smooth transitions
  useEffect(() => {
    if (markers.length > 0) {
      const latestMarker = markers[0]; // Most recent marker
      if (latestMarker.lat && latestMarker.lon) {
        // Only update if location actually changed
        if (
          !previousLocation ||
          Math.abs(previousLocation[0] - latestMarker.lat) > 0.01 ||
          Math.abs(previousLocation[1] - latestMarker.lon) > 0.01
        ) {
          setPreviousLocation([latestMarker.lat, latestMarker.lon]);
        }
      }
    }
  }, [markers, previousLocation]);

  // Determine if map interaction/zoom should be enabled (only when at least one disaster marker exists)
  const enableMapInteraction = useMemo(() => {
    return markers.some((m) => m.disaster_label === 1);
  }, [markers]);

  // Calculate initial center and zoom
  const { initialCenter, initialZoom } = useMemo(() => {
    if (markers.length === 1) {
      return {
        initialCenter: [markers[0].lat, markers[0].lon],
        initialZoom: 13,
      };
    } else if (markers.length > 1) {
      // Center on average of all markers
      const avgLat =
        markers.reduce((sum, m) => sum + m.lat, 0) / markers.length;
      const avgLon =
        markers.reduce((sum, m) => sum + m.lon, 0) / markers.length;
      return {
        initialCenter: [avgLat, avgLon],
        initialZoom: 6,
      };
    }
    return {
      initialCenter: defaultCenter,
      initialZoom: 4,
    };
  }, [markers]);

  // Debug: Log markers and results for troubleshooting
  useEffect(() => {
    if (process.env.NODE_ENV === "development") {
      console.log("🗺️ DisasterMap Component:");
      console.log("  - Results received:", resultsArray);
      console.log("  - Results count:", resultsArray.length);
      console.log("  - Markers found:", markers.length);
      if (markers.length > 0) {
        console.log("  - Markers:", markers);
        console.log("  - Initial center:", initialCenter);
        console.log("  - Initial zoom:", initialZoom);
      } else if (resultsArray.length > 0) {
        console.log(
          "  - Results without valid coordinates:",
          resultsArray.map((r) => ({
            hasLat: r?.lat != null,
            hasLon: r?.lon != null,
            lat: r?.lat,
            lon: r?.lon,
            location_mention: r?.location_mention,
            location: r?.location,
          }))
        );
      }
    }
  }, [resultsArray, markers, initialCenter, initialZoom]);

  return (
    <div className="card map-card">
      <div className="card-header">
        <h2>🗺️ Map Visualization</h2>
        <p className="subtitle">Interactive disaster location mapping</p>
      </div>
      <div
        style={{
          marginBottom: "12px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "12px",
          flexWrap: "wrap",
        }}
      >
        {markers.length > 0 && (
          <div
            style={{
              padding: "10px 14px",
              background: "rgba(99, 102, 241, 0.1)",
              border: "1px solid rgba(99, 102, 241, 0.2)",
              borderRadius: "8px",
              display: "flex",
              alignItems: "center",
              gap: "8px",
              fontSize: "0.9rem",
              color: "#a5b4fc",
              fontWeight: 500,
            }}
          >
            <span>📍</span>
            <span>
              {markers.length} location{markers.length > 1 ? "s" : ""} detected
            </span>
          </div>
        )}
        {clusters.length > 0 && (
          <label
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              fontSize: "0.9rem",
              color: "#cbd5e1",
              cursor: "pointer",
              userSelect: "none",
            }}
          >
            <input
              type="checkbox"
              checked={showClusters}
              onChange={(e) => setShowClusters(e.target.checked)}
              style={{ cursor: "pointer" }}
            />
            <span>Show Clusters ({clusters.length})</span>
          </label>
        )}
        <div style={{ display: "flex", gap: "8px" }}>
          <button
            onClick={() => {
              if (enableMapInteraction && zoomInRef.current) {
                zoomInRef.current();
              }
            }}
            disabled={!enableMapInteraction}
            style={{
              padding: "8px 16px",
              background: enableMapInteraction
                ? "rgba(16, 185, 129, 0.1)"
                : "rgba(100, 116, 139, 0.06)",
              border: enableMapInteraction
                ? "1px solid rgba(16, 185, 129, 0.3)"
                : "1px solid rgba(148,163,184,0.08)",
              borderRadius: "8px",
              color: enableMapInteraction ? "#10b981" : "#94a3b8",
              fontSize: "0.9rem",
              fontWeight: 500,
              cursor: enableMapInteraction ? "pointer" : "not-allowed",
              transition: "all 0.2s ease",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
            onMouseEnter={(e) => {
              if (enableMapInteraction) {
                e.target.style.background = "rgba(16, 185, 129, 0.2)";
                e.target.style.borderColor = "rgba(16, 185, 129, 0.5)";
              }
            }}
            onMouseLeave={(e) => {
              if (enableMapInteraction) {
                e.target.style.background = "rgba(16, 185, 129, 0.1)";
                e.target.style.borderColor = "rgba(16, 185, 129, 0.3)";
              }
            }}
          >
            <span>🔍</span>
            <span>Zoom In</span>
          </button>
          <button
            onClick={() => {
              if (enableMapInteraction && zoomOutRef.current) {
                zoomOutRef.current();
              }
            }}
            disabled={!enableMapInteraction}
            style={{
              padding: "8px 16px",
              background: enableMapInteraction
                ? "rgba(99, 102, 241, 0.1)"
                : "rgba(100, 116, 139, 0.06)",
              border: enableMapInteraction
                ? "1px solid rgba(99, 102, 241, 0.3)"
                : "1px solid rgba(148,163,184,0.08)",
              borderRadius: "8px",
              color: enableMapInteraction ? "#a5b4fc" : "#94a3b8",
              fontSize: "0.9rem",
              fontWeight: 500,
              cursor: enableMapInteraction ? "pointer" : "not-allowed",
              transition: "all 0.2s ease",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
            onMouseEnter={(e) => {
              if (enableMapInteraction) {
                e.target.style.background = "rgba(99, 102, 241, 0.2)";
                e.target.style.borderColor = "rgba(99, 102, 241, 0.5)";
              }
            }}
            onMouseLeave={(e) => {
              if (enableMapInteraction) {
                e.target.style.background = "rgba(99, 102, 241, 0.1)";
                e.target.style.borderColor = "rgba(99, 102, 241, 0.3)";
              }
            }}
          >
            <span>🔍</span>
            <span>Zoom Out</span>
          </button>
        </div>
      </div>
      <div
        className="map-container-wrapper"
        style={{
          position: "relative",
          width: "100%",
          height: "380px",
          minHeight: "380px",
          backgroundColor: "#1e293b",
          borderRadius: "8px",
          overflow: "hidden",
        }}
      >
        <MapContainer
          center={initialCenter}
          zoom={initialZoom}
          style={{ height: "100%", width: "100%", zIndex: 0 }}
          scrollWheelZoom={true}
          key={`map-${markers.length}-${initialCenter[0]}-${initialCenter[1]}`}
          whenCreated={(mapInstance) => {
            // Force map to invalidate size after creation
            setTimeout(() => {
              if (mapInstance) {
                mapInstance.invalidateSize();
              }
            }, 100);
          }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            maxZoom={19}
            errorTileUrl=""
            noWrap={false}
          />
          <MapController
            markers={markers}
            previousLocation={previousLocation}
            onZoomOut={zoomOutRef}
            onZoomIn={zoomInRef}
            enableInteraction={enableMapInteraction}
          />
          <ZoomControl position="bottomright" />

          {/* Cluster Circles */}
          {showClusters &&
            clusters.map((cluster) => {
              if (!cluster.center_lat || !cluster.center_lon) return null;

              const getClusterColor = (alertLevel) => {
                switch (alertLevel) {
                  case "Critical":
                    return "#dc2626";
                  case "High":
                    return "#ef4444";
                  case "Medium":
                    return "#f59e0b";
                  default:
                    return "#6366f1";
                }
              };

              const radius = Math.max(500, cluster.tweet_count * 200); // Scale with tweet count

              return (
                <Circle
                  key={`cluster-${cluster.id}`}
                  center={[cluster.center_lat, cluster.center_lon]}
                  radius={radius}
                  pathOptions={{
                    color: getClusterColor(cluster.alert_level),
                    fillColor: getClusterColor(cluster.alert_level),
                    fillOpacity: 0.2,
                    weight: 2,
                  }}
                >
                  <Popup>
                    <div style={{ textAlign: "left", minWidth: "200px" }}>
                      <div
                        style={{
                          marginBottom: "8px",
                          paddingBottom: "8px",
                          borderBottom: "1px solid rgba(0,0,0,0.1)",
                        }}
                      >
                        <strong
                          style={{
                            fontSize: "1.1rem",
                            color: getClusterColor(cluster.alert_level),
                          }}
                        >
                          {cluster.category || "Disaster Cluster"}
                        </strong>
                        <span
                          style={{
                            marginLeft: "6px",
                            padding: "2px 8px",
                            background: getClusterColor(cluster.alert_level),
                            color: "white",
                            borderRadius: "4px",
                            fontSize: "0.75rem",
                            fontWeight: 700,
                          }}
                        >
                          {cluster.alert_level}
                        </span>
                      </div>
                      <div style={{ marginBottom: "6px", fontSize: "0.9rem" }}>
                        <strong>📊 Reports:</strong> {cluster.tweet_count}
                      </div>
                      <div style={{ marginBottom: "6px", fontSize: "0.9rem" }}>
                        <strong>⭐ Credibility:</strong>{" "}
                        <span style={{ fontWeight: 600, color: "#6366f1" }}>
                          {(cluster.credibility_score * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div style={{ marginBottom: "6px", fontSize: "0.9rem" }}>
                        <strong>⚡ Severity:</strong>{" "}
                        {cluster.severity || "Unknown"}
                      </div>
                      <div
                        style={{
                          fontSize: "0.85rem",
                          color: "#64748b",
                          fontFamily: "monospace",
                          marginTop: "8px",
                          paddingTop: "8px",
                          borderTop: "1px solid rgba(0,0,0,0.1)",
                        }}
                      >
                        <strong>📍 Center:</strong>
                        <br />
                        {cluster.center_lat.toFixed(4)},{" "}
                        {cluster.center_lon.toFixed(4)}
                      </div>
                    </div>
                  </Popup>
                </Circle>
              );
            })}

          {/* Individual Tweet Markers */}
          {markers.map((r, idx) => {
            if (!r.lat || !r.lon) return null;
            return (
              <Marker
                key={`marker-${idx}-${r.lat}-${r.lon}`}
                position={[r.lat, r.lon]}
              >
                <Popup>
                  <div
                    style={{
                      textAlign: "left",
                      minWidth: "220px",
                      padding: "4px",
                    }}
                  >
                    <div
                      style={{
                        marginBottom: "8px",
                        paddingBottom: "8px",
                        borderBottom: "1px solid rgba(0,0,0,0.1)",
                      }}
                    >
                      <strong
                        style={{
                          fontSize: "1.1rem",
                          color: r.disaster_label ? "#ef4444" : "#10b981",
                        }}
                      >
                        {r.category || "Disaster"}
                      </strong>
                      <span
                        style={{
                          marginLeft: "6px",
                          fontSize: "0.85rem",
                          color: "#64748b",
                        }}
                      >
                        ({r.severity || "Unknown"})
                      </span>
                    </div>
                    <div style={{ marginBottom: "6px", fontSize: "0.9rem" }}>
                      <strong>📍 Location:</strong>
                      <br />
                      <span style={{ color: "#475569" }}>
                        {r.location || r.location_mention || "Unknown location"}
                      </span>
                    </div>
                    <div style={{ marginBottom: "6px", fontSize: "0.9rem" }}>
                      <strong>🎯 Status:</strong>{" "}
                      <span
                        style={{
                          color: r.disaster_label ? "#ef4444" : "#10b981",
                          fontWeight: 600,
                        }}
                      >
                        {r.disaster_text}
                      </span>
                    </div>
                    <div style={{ marginBottom: "6px", fontSize: "0.9rem" }}>
                      <strong>📊 Confidence:</strong>{" "}
                      <span style={{ fontWeight: 600, color: "#6366f1" }}>
                        {(
                          r.confidence_percentage || r.confidence * 100
                        ).toFixed(1)}
                        %
                      </span>
                    </div>
                    <div
                      style={{
                        fontSize: "0.85rem",
                        color: "#64748b",
                        fontFamily: "monospace",
                        marginTop: "8px",
                        paddingTop: "8px",
                        borderTop: "1px solid rgba(0,0,0,0.1)",
                      }}
                    >
                      <strong>Coordinates:</strong>
                      <br />
                      {r.lat.toFixed(4)}, {r.lon.toFixed(4)}
                    </div>
                  </div>
                </Popup>
              </Marker>
            );
          })}
        </MapContainer>
      </div>
      {markers.length === 0 && resultsArray.length > 0 && (
        <div
          style={{
            marginTop: 8,
            padding: "12px",
            backgroundColor: "rgba(239, 68, 68, 0.1)",
            borderRadius: "8px",
          }}
        >
          <p style={{ textAlign: "center", color: "#ef4444", margin: 0 }}>
            ⚠️ No location detected in analyzed tweets.
            <br />
            <span style={{ fontSize: "0.9rem", color: "#64748b" }}>
              Try: "Fire in New York" or "Earthquake at 40.7128, -74.0060"
            </span>
          </p>
        </div>
      )}
      {markers.length === 0 && resultsArray.length === 0 && (
        <p style={{ marginTop: 8, textAlign: "center", color: "#64748b" }}>
          📍 No tweets analyzed yet.
          <br />
          Analyze a tweet mentioning a place to see it on the map.
        </p>
      )}
    </div>
  );
}

export default DisasterMap;
