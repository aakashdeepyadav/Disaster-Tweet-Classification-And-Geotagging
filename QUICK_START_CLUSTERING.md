# ⚠️ DEPRECATED — Moved to `README.md`

This file has been merged into the main `README.md` under the "Clustering & Alerts" section.

**Please consult `README.md` for usage, API endpoints, and troubleshooting for clustering and alert features.**

## Installation

### Step 1: Install Dependencies

```bash
cd backend
.\venv\Scripts\Activate.ps1  # or: source venv/bin/activate
pip install sqlalchemy scipy
```

### Step 2: Start Backend

```bash
python run.py
```

The database will be automatically created on first run at `backend/disaster_tweets.db`

### Step 3: Start Frontend

```bash
cd frontend/disaster-frontend
npm run dev
```

## How to Use

### 1. Analyze Tweets

Enter tweets with locations, for example:

- "Massive flood in New York, NY! Streets are flooded!"
- "Flooding in Manhattan, New York. Water everywhere!"
- "Serious flood in NYC, multiple areas affected"

### 2. View Clusters

- Clusters automatically appear on the map as colored circles
- Circle size = number of tweets in cluster
- Circle color = alert level (Red=Critical, Orange=High, etc.)

### 3. View Alerts

- **AlertsPanel** (top right) shows serious alerts
- Alerts appear when multiple people report same disaster in same area
- Credibility score shows how reliable the alert is

### 4. Toggle Clusters

- Use checkbox on map to show/hide clusters
- Individual tweet markers always visible

## Understanding Credibility

**High Credibility (≥0.7)** = Multiple people reporting same disaster in same area

- More tweets = higher credibility
- Same category = higher credibility
- High confidence = higher credibility

**Alert Levels:**

- 🚨 **Critical**: 5+ tweets, High severity, Credibility ≥0.8
- ⚠️ **High**: 3+ tweets, Credibility ≥0.6
- ⚡ **Medium**: 2+ tweets, Credibility ≥0.4
- ℹ️ **Low**: Single tweet or low credibility

## Example Scenario

1. Analyze: "Flood in New York, NY"
2. Analyze: "Flooding in Manhattan, New York"
3. Analyze: "Serious flood in NYC"
4. Analyze: "Flood in New York City"
5. Analyze: "Major flooding in New York, NY"

**Result:**

- ✅ 5 tweets cluster together
- ✅ Credibility: ~85%
- ✅ Alert Level: **Critical**
- ✅ Red circle on map
- ✅ Alert in AlertsPanel

## API Endpoints

- `GET /clusters` - Get all clusters
- `GET /alerts?min_credibility=0.7` - Get serious alerts
- `GET /stats` - Get statistics

## Troubleshooting

**Database not working?**

```bash
pip install sqlalchemy scipy
```

**No clusters showing?**

- Make sure tweets have location coordinates
- Analyze multiple tweets about same disaster in same area
- Check browser console for errors

**Alerts not appearing?**

- Need at least 2 tweets in same cluster
- Credibility must be ≥0.7 for alerts
- Check `/alerts` endpoint directly

---

**That's it! The system automatically clusters tweets and generates alerts when multiple people report the same disaster!** 🎯
