# Disaster Tweet Classification and Geotagging

> Detect disaster-related tweets, estimate severity, extract locations, and visualize them on a map.

A compact full-stack NLP application built with **DistilBERT**, **Flask**, and **React**. The system classifies tweets as disaster or non-disaster, derives risk signals, geotags location mentions, and renders map previews when coordinates are available.

## Overview

**Core capabilities**

- Disaster vs non-disaster classification with confidence score
- Category, severity, and risk-level inference
- Location extraction from tweet text
- Name-to-coordinate geocoding with online and offline fallback
- OpenStreetMap preview for geotagged disaster tweets
- Session-based recent prediction history in the frontend

**Tech stack**

- Backend: Flask, PyTorch, Transformers, geopy
- Frontend: React, Vite
- Model: fine-tuned DistilBERT checkpoint in `backend/models/best_model`

## How It Works

1. User submits a tweet from the frontend.
2. The Flask API preprocesses the text and runs model inference.
3. The backend infers category, severity, and risk level.
4. If the tweet is classified as a disaster, geotagging tries to extract coordinates or resolve a location name.
5. The frontend displays the result and shows a map only when valid coordinates exist.

## Project Structure

```text
backend/
  app.py              Flask API entry point
  geotagging.py       Location extraction and geocoding
  model_loader.py     Loads the saved model
  preprocessing.py    Text cleaning pipeline
  utils.py            Category and severity helpers
  requirements.txt
  models/
    best_model/       Ready-to-use DistilBERT checkpoint

frontend/
  src/
    App.jsx           Main user interface
    App.css           Application styles
```

## Quick Start

### Backend

Use **Python 3.12** for best compatibility.

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Backend URL: `http://localhost:5000`

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend URL: usually `http://localhost:5173`

If your backend is hosted elsewhere, add `frontend/.env`:

```env
VITE_API_URL=http://localhost:5000
```

## API Reference

| Method | Endpoint         | Purpose                                |
| ------ | ---------------- | -------------------------------------- |
| GET    | `/` or `/health` | Service health and model availability  |
| POST   | `/predict`       | Classify and geotag a tweet            |
| POST   | `/geocode`       | Convert a location name to coordinates |

### Example Prediction Request

```json
{ "text": "Massive flood near Yamuna in Delhi, roads are blocked." }
```

### Example Prediction Response

```json
{
  "disaster_label": 1,
  "disaster_text": "[DISASTER] Disaster Detected",
  "confidence_percentage": 98.66,
  "category": "Flood",
  "severity": "High",
  "risk_level": "Critical",
  "location": "Delhi, IN",
  "location_mention": "Delhi",
  "lat": 28.65195,
  "lon": 77.23149,
  "geotag_source": "geocoding",
  "model_info": {
    "model_name": "distilbert-base-uncased"
  },
  "processing_time_ms": 60.1,
  "status": "success"
}
```

## Notes

- The map appears only for disaster predictions with valid coordinates.
- Location geocoding supports online providers plus offline fallback for common city names.
- Training scripts and temporary research artifacts were intentionally removed to keep this repo deployment-focused.

## Deployment

### What gets deployed

- Frontend: static Vite app on Vercel
- Backend: Flask API on Render
- Main production endpoints:
  - `GET /health` or `GET /`
  - `POST /predict`

### Deploy Backend on Render

1. Push the repository to GitHub.
2. In Render, create a new Web Service and connect the repo.
3. Use these settings:

- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt ; python -m spacy download en_core_web_sm`
- Start Command: `gunicorn -w 1 -b 0.0.0.0:$PORT app:app`

4. Set environment variables:

- `PYTHON_VERSION=3.10.13`
- `FLASK_ENV=production`

5. Deploy and verify the health endpoint:

- `https://your-backend.onrender.com/health`

### Deploy Frontend on Vercel

1. Create a new Vercel project from the same GitHub repo.
2. Use these settings:

- Root Directory: `frontend`
- Build Command: `npm run build`
- Output Directory: `dist`

3. Add the environment variable:

- `VITE_API_URL=https://your-backend.onrender.com`

4. Deploy.

### Post-Deploy Check

1. Open the frontend URL.
2. Submit a sample tweet.
3. Confirm the result returns classification, confidence, and location details.

### Deployment Notes

- Render free instances can sleep after inactivity, so the first request may be slow.
- Keep `backend/models/best_model` in the deployed source.

---

Made with ❤️ by Aakash
