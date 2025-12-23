"""
Disaster Intelligence API Server

IMPORTANT: You must activate the virtual environment before running this script!

Windows (PowerShell):
    cd backend
    .\\venv\\Scripts\\Activate.ps1
    python app.py

Windows (Command Prompt):
    cd backend
    venv\\Scripts\\activate.bat
    python app.py

Linux/Mac:
    cd backend
    source venv/bin/activate
    python app.py

Or use the helper script:
    cd backend
    .\\START_SERVER.ps1  (Windows PowerShell)
    .\\START_SERVER.bat  (Windows CMD)
"""

import sys
import os

# Check if we're in a virtual environment
def check_venv():
    """Check if virtual environment is activated"""
    in_venv = (
        hasattr(sys, 'real_prefix') or 
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    )
    
    if not in_venv:
        print("="*70)
        print("ERROR: Virtual environment not activated!")
        print("="*70)
        print("\nYou need to activate the virtual environment first:")
        print("\nWindows (PowerShell):")
        print("  cd backend")
        print("  .\\venv\\Scripts\\Activate.ps1")
        print("  python app.py")
        print("\nWindows (Command Prompt):")
        print("  cd backend")
        print("  venv\\Scripts\\activate.bat")
        print("  python app.py")
        print("\nLinux/Mac:")
        print("  cd backend")
        print("  source venv/bin/activate")
        print("  python app.py")
        print("\nOr use the helper script:")
        print("  cd backend")
        print("  .\\START_SERVER.ps1")
        print("="*70)
        sys.exit(1)

# Check for virtual environment before importing
check_venv()

from flask import Flask, request, jsonify
from flask_cors import CORS
import torch
from utils import infer_category, infer_severity
from preprocessing import clean_text
from model_loader import load_model
import logging
from functools import wraps
from datetime import datetime
# Import database and clustering modules (optional - graceful degradation)
try:
    from database import (
        init_database, save_tweet, get_recent_tweets, get_tweets_with_location,
        save_cluster, link_tweet_to_cluster, get_clusters, get_serious_alerts,
        clear_all_data
    )
    from clustering import process_clusters
    DB_AVAILABLE = True
except ImportError as e:
    print(f"[WARNING] Database/clustering modules not available: {e}")
    print("   Install SQLAlchemy: pip install sqlalchemy")
    DB_AVAILABLE = False
    
    # Dummy functions for graceful degradation
    def init_database():
        pass
    def save_tweet(*args, **kwargs):
        return None
    def get_recent_tweets(*args, **kwargs):
        return []
    def get_tweets_with_location(*args, **kwargs):
        return []
    def save_cluster(*args, **kwargs):
        return None
    def link_tweet_to_cluster(*args, **kwargs):
        pass
    def get_clusters(*args, **kwargs):
        return []
    def get_serious_alerts(*args, **kwargs):
        return []
    def process_clusters(*args, **kwargs):
        return []
    def clear_all_data(*args, **kwargs):
        return {"tweets_deleted": 0, "clusters_deleted": 0, "total_deleted": 0}

# Try to import geotagging, but make it optional if spaCy fails.
# If spaCy isn't available, we still want coordinate parsing to work.
try:
    from geotagging import extract_location, geocode_location, extract_and_geocode, extract_coordinates
    GEOTAGGING_AVAILABLE = True
except Exception as e:
    import re
    print(f"[WARNING] Geotagging not available (spaCy issue): {e}")
    print("   Location name extraction disabled, but coordinates will still be parsed.")
    GEOTAGGING_AVAILABLE = False

    def extract_location(text):
        return None

    def geocode_location(location_str, default_country=None):
        return None

    def extract_coordinates(text):
        # Minimal fallback coordinate extractor (lat, lon)
        pattern = r'(-?\\d+\\.?\\d+)\\s*[,;]\\s*(-?\\d+\\.?\\d+)'
        matches = re.findall(pattern, text)
        if matches:
            try:
                lat = float(matches[0][0]); lon = float(matches[0][1])
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return (lat, lon)
            except ValueError:
                pass
        return None

    def extract_and_geocode(text: str):
        result = {
            "location_mention": None,
            "location": None,
            "lat": None,
            "lon": None,
            "source": None
        }
        coords = extract_coordinates(text)
        if coords:
            lat, lon = coords
            result["lat"] = lat
            result["lon"] = lon
            result["location_mention"] = f"{lat:.4f}, {lon:.4f}"
            result["location"] = f"Coordinates: {lat:.4f}, {lon:.4f}"
            result["source"] = "coordinates"
        return result

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Request logging decorator
def log_request(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.info(f"Request: {request.method} {request.path}")
        return f(*args, **kwargs)
    return decorated_function

# Initialize database
if DB_AVAILABLE:
    print("="*60)
    print("INITIALIZING DATABASE")
    print("="*60)
    try:
        init_database()
        print("[READY] Database initialized successfully!")
    except Exception as e:
        print(f"[WARNING] Database initialization error: {e}")
        print("Continuing without database features...")
        DB_AVAILABLE = False
else:
    print("[WARNING] Database features disabled (SQLAlchemy not installed)")

# Auto-load best model (can be disabled for tests)
print("="*60)
print("INITIALIZING DISASTER INTELLIGENCE API")
print("="*60)
if os.environ.get("DISABLE_AUTO_LOAD_MODEL") == "1":
    print("[INFO] Auto model loading disabled (DISABLE_AUTO_LOAD_MODEL=1)")
    model = None
    tokenizer = None
    model_info = None
    MAX_LEN = 128
    device = torch.device("cpu")
else:
    try:
        model, tokenizer, model_info = load_model()
        MAX_LEN = model_info.get("config", {}).get("max_length", 128) if model_info else 128
        device = next(model.parameters()).device
        print("="*60)
        print("[READY] API READY - Best model loaded successfully!")
        print("="*60)
    except Exception as e:
        print(f"[ERROR] Error loading model: {e}")
        print("Please run: python train_advanced.py")
        raise

def predict_single(text: str):
    """Predict disaster classification for a single tweet"""
    # Clean the input text using the same preprocessing as training
    cleaned_text = clean_text(text)
    full_text = cleaned_text
    
    # Tokenize
    enc = tokenizer(
        full_text,
        truncation=True,
        padding="max_length",
        max_length=MAX_LEN,
        return_tensors="pt",
    )
    enc = {k: v.to(device) for k, v in enc.items()}
    
    # Predict
    with torch.no_grad():
        outputs = model(**enc)
        logits = outputs.logits
        probs = torch.softmax(logits, dim=-1)
        confidence, pred_class = torch.max(probs, dim=-1)
        is_disaster = int(pred_class.item())
        conf = float(confidence.item())
        # Get probability for disaster class
        disaster_prob = float(probs[0][1].item())

    # Infer category and severity
    category = infer_category(text)
    severity = infer_severity(text)

    # Extract and geocode location (if available) — only for disasters
    loc_mention = None
    geo = None
    lat = None
    lon = None

    if is_disaster == 1:
        # Try geotagging only when the tweet is predicted as a disaster
        logger.info(f"[GEO] Starting geotagging for text: {text[:100]}")
        try:
            geo_result = extract_and_geocode(text)

            # Extract all values from result
            loc_mention = geo_result.get("location_mention")
            location_name = geo_result.get("location")
            lat = geo_result.get("lat")
            lon = geo_result.get("lon")
            source = geo_result.get("source")

            logger.info(f"[GEO] Geotagging result: lat={lat}, lon={lon}, mention={loc_mention}, location={location_name}, source={source}")

            # Build geo object if we have coordinates
            if lat is not None and lon is not None:
                geo = {
                    "name": location_name or loc_mention or f"Coordinates: {lat:.4f}, {lon:.4f}",
                    "lat": lat,
                    "lon": lon
                }
                logger.info(f"[GEO] ✅ Successfully extracted coordinates: {lat}, {lon}")
            else:
                logger.warning(f"[GEO] ⚠️ No coordinates extracted from text")

        except Exception as e:
            logger.error(f"[GEO] Geotagging error: {e}", exc_info=True)
            # If spaCy fails but we can still extract coordinates, try that
            try:
                logger.info("[GEO] Attempting fallback coordinate extraction...")
                coords = extract_coordinates(text)
                if coords:
                    lat, lon = coords
                    loc_mention = f"{lat:.4f}, {lon:.4f}"
                    geo = {
                        "name": f"Coordinates: {lat:.4f}, {lon:.4f}",
                        "lat": lat,
                        "lon": lon
                    }
                    logger.info(f"[GEO] ✅ Fallback successful: Extracted coordinates directly: {lat}, {lon}")
                else:
                    logger.warning("[GEO] ❌ Fallback also failed: No coordinates found")
            except Exception as coord_error:
                logger.error(f"[GEO] Coordinate extraction fallback failed: {coord_error}", exc_info=True)
    else:
        logger.info("[GEO] Skipping geotagging for non-disaster prediction")

    # Determine risk level based on confidence and severity
    risk_level = "Low"
    if is_disaster == 1:
        if conf >= 0.9 or severity == "High":
            risk_level = "Critical"
        elif conf >= 0.75 or severity == "Medium":
            risk_level = "High"
        else:
            risk_level = "Medium"

    # Final validation and logging
    final_lat = float(lat) if lat is not None else None
    final_lon = float(lon) if lon is not None else None
    
    location_name = geo['name'] if geo else None
    logger.info(f"[RESULT] Final location data: lat={final_lat}, lon={final_lon}, mention={loc_mention}, location={location_name}")
    
    if final_lat and final_lon:
        logger.info(f"[RESULT] ✅ Location successfully extracted: {final_lat}, {final_lon}")
    else:
        logger.warning(f"[RESULT] ⚠️ No location coordinates in result")

    return {
        "tweet": text,
        "disaster_label": is_disaster,
        "disaster_text": "[DISASTER] Disaster Detected" if is_disaster == 1 else "[SAFE] Not a Disaster",
        "confidence": conf,
        "confidence_percentage": round(conf * 100, 2),
        "disaster_probability": round(disaster_prob * 100, 2),
        "category": category,
        "severity": severity,
        "risk_level": risk_level,
        "location_mention": loc_mention,
        "location": geo["name"] if geo else None,
        "lat": final_lat,
        "lon": final_lon,
        "model_info": {
            "model_name": model_info.get("model_name", "Unknown"),
            "accuracy": model_info.get("best_metrics", {}).get("accuracy", 0),
            "f1_score": model_info.get("best_metrics", {}).get("f1_score", 0),
        } if model_info else None,
    }

@app.route("/", methods=["GET"])
@log_request
def health_check():
    """Health check endpoint"""
    try:
        return jsonify({
            "status": "online",
            "service": "Disaster Intelligence API",
            "model_loaded": model is not None,
            "model_info": model_info if model_info else None,
            "geotagging_available": GEOTAGGING_AVAILABLE,
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route("/test-geo", methods=["POST"])
def test_geotagging():
    """Test endpoint for geotagging"""
    try:
        data = request.get_json()
        text = data.get("text", "")
        
        from geotagging import extract_and_geocode, extract_coordinates
        result = extract_and_geocode(text)
        coords_direct = extract_coordinates(text)
        
        return jsonify({
            "text": text,
            "extract_and_geocode": result,
            "extract_coordinates_direct": coords_direct,
            "status": "success"
        })
    except Exception as e:
        import traceback
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc(),
            "status": "error"
        }), 500

@app.route("/predict", methods=["POST"])
@log_request
def predict_endpoint():
    """Single tweet prediction endpoint"""
    try:
        data = request.get_json()
        if not data:
            logger.warning("No data provided in request")
            return jsonify({"error": "No data provided", "status": "error"}), 400
        
        text = data.get("text", "")
        if not text or not text.strip():
            logger.warning("Empty text provided")
            return jsonify({
                "error": "No text provided",
                "status": "error",
                "message": "Please provide a tweet text in the 'text' field"
            }), 400

        start_time = datetime.utcnow()
        result = predict_single(text.strip())
        result["status"] = "success"
        result["processing_time_ms"] = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Save tweet to database (if available)
        if DB_AVAILABLE:
            try:
                tweet_id = save_tweet(result)
                if tweet_id:
                    result["tweet_id"] = tweet_id
                    logger.info(f"Tweet saved to database with ID: {tweet_id}")
                    
                    # If it's a disaster with location, trigger clustering
                    if result.get("disaster_label") == 1 and result.get("lat") and result.get("lon"):
                        try:
                            _update_clusters()
                        except Exception as cluster_error:
                            logger.warning(f"Clustering error (non-fatal): {cluster_error}")
            except Exception as db_error:
                logger.warning(f"Database save error (non-fatal): {db_error}")
        
        logger.info(f"Prediction successful: disaster={result.get('disaster_label')}, confidence={result.get('confidence_percentage')}%")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        return jsonify({
            "error": str(e),
            "status": "error",
            "message": "An error occurred during prediction"
        }), 500

def _update_clusters():
    """Internal function to update clusters based on recent tweets"""
    try:
        # Get recent disaster tweets with locations
        tweets = get_tweets_with_location(disaster_only=True)
        if len(tweets) < 1:
            return
        
        # Process clusters
        clusters = process_clusters(tweets)
        
        # Save clusters to database
        for cluster in clusters:
            cluster_id = save_cluster(cluster)
            # Link tweets to cluster
            for tweet in cluster.get("tweets", []):
                if tweet.get("id"):
                    link_tweet_to_cluster(cluster_id, tweet["id"])
        
        logger.info(f"Updated {len(clusters)} clusters")
    except Exception as e:
        logger.error(f"Error updating clusters: {e}", exc_info=True)


@app.route("/clusters", methods=["GET"])
@log_request
def get_clusters_endpoint():
    """Get all clusters"""
    if not DB_AVAILABLE:
        return jsonify({
            "error": "Database not available",
            "status": "error",
            "message": "Please install SQLAlchemy: pip install sqlalchemy"
        }), 503
    try:
        alert_level = request.args.get("alert_level")  # Optional filter
        clusters = get_clusters(alert_level=alert_level)
        
        # Convert to JSON-serializable format
        result = []
        for cluster in clusters:
            cluster_dict = {
                "id": cluster.get("id"),
                "cluster_type": cluster.get("cluster_type"),
                "center_lat": cluster.get("center_lat"),
                "center_lon": cluster.get("center_lon"),
                "category": cluster.get("category"),
                "severity": cluster.get("severity"),
                "tweet_count": cluster.get("tweet_count"),
                "credibility_score": round(cluster.get("credibility_score", 0), 3),
                "alert_level": cluster.get("alert_level"),
                "created_at": cluster.get("created_at"),
            }
            result.append(cluster_dict)
        
        return jsonify({
            "status": "success",
            "clusters": result,
            "count": len(result)
        })
    except Exception as e:
        logger.error(f"Error getting clusters: {e}", exc_info=True)
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500


@app.route("/alerts", methods=["GET"])
@log_request
def get_alerts_endpoint():
    """Get serious disaster alerts"""
    if not DB_AVAILABLE:
        return jsonify({
            "error": "Database not available",
            "status": "error",
            "message": "Please install SQLAlchemy: pip install sqlalchemy"
        }), 503
    try:
        min_credibility = float(request.args.get("min_credibility", 0.7))
        alerts = get_serious_alerts(min_credibility=min_credibility)
        
        # Format alerts
        result = []
        for alert in alerts:
            alert_dict = {
                "id": alert.get("id"),
                "category": alert.get("category"),
                "severity": alert.get("severity"),
                "location": {
                    "lat": alert.get("center_lat"),
                    "lon": alert.get("center_lon")
                },
                "tweet_count": alert.get("tweet_count"),
                "credibility_score": round(alert.get("credibility_score", 0), 3),
                "alert_level": alert.get("alert_level"),
                "tweets": [
                    {
                        "id": t.get("id"),
                        "text": t.get("tweet_text"),
                        "confidence": t.get("confidence"),
                        "created_at": t.get("created_at")
                    }
                    for t in alert.get("tweets", [])[:5]  # Limit to 5 most recent
                ]
            }
            result.append(alert_dict)
        
        return jsonify({
            "status": "success",
            "alerts": result,
            "count": len(result)
        })
    except Exception as e:
        logger.error(f"Error getting alerts: {e}", exc_info=True)
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500


@app.route("/tweets", methods=["GET"])
@log_request
def get_tweets_endpoint():
    """Get recent tweets from the database"""
    if not DB_AVAILABLE:
        return jsonify({
            "error": "Database not available",
            "status": "error",
            "message": "Please install SQLAlchemy: pip install sqlalchemy"
        }), 503
    try:
        limit = int(request.args.get("limit", 100))
        disaster_only = request.args.get("disaster_only", "false").lower() == "true"
        
        tweets = get_recent_tweets(limit=limit, disaster_only=disaster_only)
        
        # Convert to frontend-compatible format
        result = []
        for tweet in tweets:
            tweet_dict = {
                "tweet": tweet.get("tweet_text"),
                "disaster_label": tweet.get("disaster_label", 0),
                "disaster_text": "[DISASTER] Disaster Detected" if tweet.get("disaster_label") == 1 else "[SAFE] Not a Disaster",
                "confidence": tweet.get("confidence", 0.0),
                "confidence_percentage": round(tweet.get("confidence", 0.0) * 100, 2),
                "disaster_probability": round(tweet.get("confidence", 0.0) * 100, 2),
                "category": tweet.get("category"),
                "severity": tweet.get("severity"),
                "risk_level": tweet.get("risk_level"),
                "location_mention": tweet.get("location_mention"),
                "location": tweet.get("location"),
                "lat": tweet.get("lat"),
                "lon": tweet.get("lon"),
                "model_info": {
                    "model_name": tweet.get("model_name"),
                    "accuracy": 0,
                    "f1_score": 0,
                } if tweet.get("model_name") else None,
                "created_at": tweet.get("created_at"),
                "id": tweet.get("id")
            }
            result.append(tweet_dict)
        
        return jsonify({
            "status": "success",
            "tweets": result,
            "count": len(result)
        })
    except Exception as e:
        logger.error(f"Error getting tweets: {e}", exc_info=True)
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500


@app.route("/stats", methods=["GET"])
@log_request
def get_stats_endpoint():
    """Get statistics about stored tweets and clusters"""
    if not DB_AVAILABLE:
        return jsonify({
            "error": "Database not available",
            "status": "error",
            "message": "Please install SQLAlchemy: pip install sqlalchemy"
        }), 503
    try:
        all_tweets = get_recent_tweets(limit=10000, disaster_only=False)
        disaster_tweets = [t for t in all_tweets if t.get("disaster_label") == 1]
        clusters = get_clusters()
        
        stats = {
            "total_tweets": len(all_tweets),
            "disaster_tweets": len(disaster_tweets),
            "safe_tweets": len(all_tweets) - len(disaster_tweets),
            "total_clusters": len(clusters),
            "critical_alerts": len([c for c in clusters if c.get("alert_level") == "Critical"]),
            "high_alerts": len([c for c in clusters if c.get("alert_level") == "High"]),
            "tweets_with_location": len([t for t in disaster_tweets if t.get("lat") and t.get("lon")])
        }
        
        return jsonify({
            "status": "success",
            "stats": stats
        })
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500


@app.route("/clear-data", methods=["POST"])
@log_request
def clear_data_endpoint():
    """Clear all data from the database (tweets, clusters, mappings)"""
    if not DB_AVAILABLE:
        return jsonify({
            "error": "Database not available",
            "status": "error",
            "message": "Please install SQLAlchemy: pip install sqlalchemy"
        }), 503
    
    try:
        # Get confirmation from request body
        data = request.get_json() or {}
        confirm = data.get("confirm", False)
        
        if not confirm:
            return jsonify({
                "error": "Confirmation required",
                "status": "error",
                "message": "Please set 'confirm' to true in request body"
            }), 400
        
        # Clear all data
        result = clear_all_data()
        
        logger.warning(f"Database cleared: {result}")
        
        return jsonify({
            "status": "success",
            "message": "All data cleared successfully",
            "deleted": result
        })
    except Exception as e:
        logger.error(f"Error clearing data: {e}", exc_info=True)
        return jsonify({
            "error": str(e),
            "status": "error",
            "message": "An error occurred while clearing data"
        }), 500


@app.route("/batch_predict", methods=["POST"])
@log_request
def batch_predict_endpoint():
    """Batch prediction endpoint for multiple tweets"""
    try:
        data = request.get_json()
        if not data:
            logger.warning("No data provided in batch request")
            return jsonify({"error": "No data provided", "status": "error"}), 400
        
        tweets = data.get("tweets", [])
        if not tweets or not isinstance(tweets, list):
            logger.warning("Invalid tweets format")
            return jsonify({
                "error": "No tweets provided",
                "status": "error",
                "message": "Please provide a list of tweets in the 'tweets' field"
            }), 400

        # Limit batch size for performance
        MAX_BATCH_SIZE = 100
        if len(tweets) > MAX_BATCH_SIZE:
            logger.warning(f"Batch size {len(tweets)} exceeds max {MAX_BATCH_SIZE}, truncating")
            tweets = tweets[:MAX_BATCH_SIZE]

        start_time = datetime.utcnow()
        results = [predict_single(t) for t in tweets if t and t.strip()]
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        logger.info(f"Batch prediction successful: {len(results)} tweets processed in {processing_time:.2f}ms")
        return jsonify({
            "results": results,
            "count": len(results),
            "status": "success",
            "processing_time_ms": processing_time
        })
    except Exception as e:
        logger.error(f"Batch prediction error: {e}", exc_info=True)
        return jsonify({
            "error": str(e),
            "status": "error",
            "message": "An error occurred during batch prediction"
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    
    logger.info("="*60)
    logger.info("Starting Disaster Intelligence API")
    logger.info(f"Port: {port}")
    logger.info(f"Debug mode: {debug_mode}")
    logger.info("="*60)
    
    print(f"\n🌐 Starting Flask server on http://0.0.0.0:{port}")
    print(f"   Debug mode: {debug_mode}")
    print(f"   Environment: {os.environ.get('FLASK_ENV', 'production')}")

    # Allow tests to disable actually running the server
    if os.environ.get("DISABLE_APP_RUN") == "1":
        print("[INFO] DISABLE_APP_RUN=1 set; skipping app.run() (test mode)")
    else:
        # Production-ready server configuration
        app.run(
            host="0.0.0.0",
            port=port,
            debug=debug_mode,
            threaded=True,  # Enable threading for concurrent requests
            use_reloader=debug_mode  # Only reload in debug mode
        )

