"""
Disaster Intelligence API Server

Minimal runtime API:
- GET / and GET /health
- POST /predict
"""

import os
import sys
import logging
import re
from datetime import datetime
from functools import wraps

import torch
from flask import Flask, jsonify, request
from flask_cors import CORS

from preprocessing import clean_text
from utils import infer_category, infer_severity

try:
    from geotagging import extract_and_geocode, geocode_location
    GEOTAGGING_AVAILABLE = True
except Exception as exc:
    GEOTAGGING_AVAILABLE = False

    def extract_and_geocode(text: str):
        # Fallback: extract coordinate pairs without spaCy/geocoding.
        pattern = r"(-?\d+\.?\d+)\s*[,;]\s*(-?\d+\.?\d+)"
        matches = re.findall(pattern, text)
        if matches:
            try:
                lat = float(matches[0][0])
                lon = float(matches[0][1])
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return {
                        "location_mention": f"{lat:.4f}, {lon:.4f}",
                        "location": f"Coordinates: {lat:.4f}, {lon:.4f}",
                        "lat": lat,
                        "lon": lon,
                    }
            except ValueError:
                pass
        return {
            "location_mention": None,
            "location": None,
            "lat": None,
            "lon": None,
        }

    def geocode_location(location_str: str, default_country: str | None = None):
        _ = default_country
        if not location_str:
            return None

        pattern = r"(-?\d+\.?\d+)\s*[,;]\s*(-?\d+\.?\d+)"
        match = re.search(pattern, location_str)
        if not match:
            return None

        try:
            lat = float(match.group(1))
            lon = float(match.group(2))
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return {
                    "name": f"Coordinates: {lat:.4f}, {lon:.4f}",
                    "lat": lat,
                    "lon": lon,
                }
        except ValueError:
            return None

        return None

    logging.getLogger(__name__).warning(
        "Geotagging module unavailable, running with coordinate-only fallback: %s",
        exc,
    )


def check_venv():
    """Check if virtual environment is activated."""
    # Allow cloud runtimes (Railway/Render/etc.) to bypass local venv enforcement.
    if os.environ.get("SKIP_VENV_CHECK", "0") == "1":
        return

    in_venv = hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )

    if not in_venv:
        print("=" * 70)
        print("ERROR: Virtual environment not activated!")
        print("=" * 70)
        print("\nActivate venv and run again.")
        print("Windows (PowerShell):")
        print("  cd backend")
        print("  .\\venv\\Scripts\\Activate.ps1")
        print("  python app.py")
        print("=" * 70)
        sys.exit(1)


check_venv()

app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def log_request(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.info("Request: %s %s", request.method, request.path)
        return f(*args, **kwargs)

    return decorated_function


print("=" * 60)
print("INITIALIZING DISASTER INTELLIGENCE API")
print("=" * 60)

if os.environ.get("DISABLE_AUTO_LOAD_MODEL") == "1":
    print("[INFO] Auto model loading disabled (DISABLE_AUTO_LOAD_MODEL=1)")
    model = None
    tokenizer = None
    model_info = None
    max_len = 128
    device = torch.device("cpu")
else:
    from model_loader import load_model

    model, tokenizer, model_info = load_model()
    max_len = model_info.get("config", {}).get("max_length", 128) if model_info else 128
    device = next(model.parameters()).device
    print("=" * 60)
    print("[READY] API READY - Best model loaded successfully!")
    print("=" * 60)

app.model = model
app.tokenizer = tokenizer
app.model_info = model_info
app.MAX_LEN = max_len
app.device = device


def predict_single(text: str):
    """Predict disaster classification for a single tweet."""
    cleaned_text = clean_text(text)
    enc = app.tokenizer(
        cleaned_text,
        truncation=True,
        padding="max_length",
        max_length=app.MAX_LEN,
        return_tensors="pt",
    )
    enc = {k: v.to(app.device) for k, v in enc.items()}

    with torch.no_grad():
        outputs = app.model(**enc)
        logits = outputs.logits
        probs = torch.softmax(logits, dim=-1)
        confidence, pred_class = torch.max(probs, dim=-1)
        is_disaster = int(pred_class.item())
        conf = float(confidence.item())
        disaster_prob = float(probs[0][1].item())

    category = infer_category(text)
    severity = infer_severity(text)

    location_mention = None
    location = None
    lat = None
    lon = None
    geotag_source = None

    if is_disaster == 1:
        try:
            geo_result = extract_and_geocode(text)
            location_mention = geo_result.get("location_mention")
            location = geo_result.get("location")
            lat = geo_result.get("lat")
            lon = geo_result.get("lon")
            geotag_source = geo_result.get("source")
        except Exception as exc:
            logger.warning("Geotagging failed: %s", exc)

    risk_level = "Low"
    if is_disaster == 1:
        if conf >= 0.9 or severity == "High":
            risk_level = "Critical"
        elif conf >= 0.75 or severity == "Medium":
            risk_level = "High"
        else:
            risk_level = "Medium"

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
        "location_mention": location_mention,
        "location": location,
        "lat": float(lat) if lat is not None else None,
        "lon": float(lon) if lon is not None else None,
        "geotag_source": geotag_source,
        "model_info": {
            "model_name": app.model_info.get("model_name", "Unknown"),
            "accuracy": app.model_info.get("best_metrics", {}).get("accuracy", 0),
            "f1_score": app.model_info.get("best_metrics", {}).get("f1_score", 0),
        }
        if app.model_info
        else None,
    }


app.predict_single = predict_single


@app.route("/", methods=["GET"])
@app.route("/health", methods=["GET"])
@log_request
def health_check():
    return jsonify(
        {
            "status": "online",
            "service": "Disaster Intelligence API",
            "model_loaded": app.model is not None,
            "geotagging_available": GEOTAGGING_AVAILABLE,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


@app.route("/predict", methods=["POST"])
@log_request
def predict_endpoint():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided", "status": "error"}), 400

        text = data.get("text", "")
        if not text or not text.strip():
            return (
                jsonify(
                    {
                        "error": "No text provided",
                        "status": "error",
                        "message": "Please provide a tweet text in the 'text' field",
                    }
                ),
                400,
            )

        start_time = datetime.utcnow()
        result = predict_single(text.strip())
        result["status"] = "success"
        result["processing_time_ms"] = (
            datetime.utcnow() - start_time
        ).total_seconds() * 1000
        return jsonify(result)
    except Exception as exc:
        logger.error("Prediction error: %s", exc, exc_info=True)
        return (
            jsonify(
                {
                    "error": str(exc),
                    "status": "error",
                    "message": "An error occurred during prediction",
                }
            ),
            500,
        )


@app.route("/geocode", methods=["POST"])
@log_request
def geocode_endpoint():
    try:
        data = request.get_json() or {}
        location_text = data.get("location", "")
        default_country = data.get("default_country")

        if not location_text or not location_text.strip():
            return (
                jsonify(
                    {
                        "error": "No location provided",
                        "status": "error",
                        "message": "Please provide a location in the 'location' field",
                    }
                ),
                400,
            )

        geo = geocode_location(location_text.strip(), default_country=default_country)
        if not geo:
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "Location not found",
                        "message": "Could not convert location to coordinates",
                    }
                ),
                404,
            )

        return jsonify(
            {
                "status": "success",
                "location_mention": location_text.strip(),
                "location": geo.get("name"),
                "lat": geo.get("lat"),
                "lon": geo.get("lon"),
                "source": "geocoding",
            }
        )
    except Exception as exc:
        logger.error("Geocode error: %s", exc, exc_info=True)
        return (
            jsonify(
                {
                    "error": str(exc),
                    "status": "error",
                    "message": "An error occurred during geocoding",
                }
            ),
            500,
        )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() == "true"

    logger.info("=" * 60)
    logger.info("Starting Disaster Intelligence API")
    logger.info("Port: %s", port)
    logger.info("Debug mode: %s", debug_mode)
    logger.info("=" * 60)

    print(f"\nStarting Flask server on http://0.0.0.0:{port}")
    print(f"Debug mode: {debug_mode}")
    print(f"Environment: {os.environ.get('FLASK_ENV', 'production')}")

    if os.environ.get("DISABLE_APP_RUN") == "1":
        print("[INFO] DISABLE_APP_RUN=1 set; skipping app.run() (test mode)")
    else:
        app.run(
            host="0.0.0.0",
            port=port,
            debug=debug_mode,
            threaded=True,
            use_reloader=debug_mode,
        )
