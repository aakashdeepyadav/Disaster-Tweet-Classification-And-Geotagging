# ⚠️ DEPRECATED — Moved to `README.md`

This file has been merged into the main `README.md` under "Merged Documentation → Clustering & Alerts".

**Please consult `README.md` for full clustering details and API endpoints.**

## ✨ Overview

This feature implements intelligent clustering of disaster tweets by location and disaster type, with automatic credibility scoring and alert generation. When multiple people tweet about the same disaster in the same area, the system creates clusters and generates alerts based on credibility.

## 🎯 Key Features

### 1. **Automatic Tweet Storage**

- Every analyzed tweet is automatically saved to SQLite database
- Stores: tweet text, classification, confidence, category, severity, location, coordinates
- Enables historical analysis and clustering

### 2. **Location-Based Clustering**

- Groups tweets by geographic proximity (within 10km)
- Clusters tweets of the same disaster type in the same area
- Calculates cluster center (average coordinates)
- Uses Haversine distance for accurate geographic clustering

### 3. **Credibility Scoring System**

The system calculates credibility based on:

- **Tweet Count**: More tweets = higher credibility (logarithmic scale)
- **Category Consistency**: All same category = higher credibility
- **Average Confidence**: Higher model confidence = higher credibility
- **Severity Boost**: High severity disasters get credibility boost

**Credibility Formula:**

```
Credibility = (Count_Score × 0.4 + Consistency × 0.2 + Avg_Confidence × 0.4) × Severity_Multiplier
```

### 4. **Alert Levels**

- **Critical**: Credibility ≥ 0.8, 5+ tweets, High severity
- **High**: Credibility ≥ 0.6, 3+ tweets
- **Medium**: Credibility ≥ 0.4, 2+ tweets
- **Low**: Everything else

### 5. **Real-time Updates**

- Clusters update automatically when new disaster tweets are analyzed
- Frontend refreshes alerts every 30 seconds
- Map shows clusters as colored circles (radius based on tweet count)

## 📊 Database Schema

### Tables

1. **tweets**: Stores all analyzed tweets

   - id, tweet_text, disaster_label, confidence, category, severity
   - location_mention, location, lat, lon
   - model_name, created_at, updated_at

2. **clusters**: Stores cluster information

   - id, cluster_type, center_lat, center_lon
   - category, severity, tweet_count
   - credibility_score, alert_level
   - created_at, updated_at

3. **cluster_tweets**: Links tweets to clusters
   - cluster_id, tweet_id

## 🔌 API Endpoints

### `/clusters` (GET)

Get all clusters, optionally filtered by alert level.

**Query Parameters:**

- `alert_level` (optional): Filter by "Critical", "High", "Medium", "Low"

**Response:**

```json
{
  "status": "success",
  "clusters": [
    {
      "id": 1,
      "cluster_type": "location",
      "center_lat": 40.7128,
      "center_lon": -74.006,
      "category": "Flood",
      "severity": "High",
      "tweet_count": 5,
      "credibility_score": 0.85,
      "alert_level": "Critical"
    }
  ],
  "count": 1
}
```

### `/alerts` (GET)

Get serious disaster alerts (high credibility clusters).

**Query Parameters:**

- `min_credibility` (optional, default: 0.7): Minimum credibility score

**Response:**

```json
{
  "status": "success",
  "alerts": [
    {
      "id": 1,
      "category": "Flood",
      "severity": "High",
      "location": { "lat": 40.7128, "lon": -74.006 },
      "tweet_count": 5,
      "credibility_score": 0.85,
      "alert_level": "Critical",
      "tweets": [
        {
          "id": 1,
          "text": "Massive flood in New York...",
          "confidence": 0.95,
          "created_at": "2024-01-01 12:00:00"
        }
      ]
    }
  ],
  "count": 1
}
```

### `/stats` (GET)

Get statistics about stored tweets and clusters.

**Response:**

```json
{
  "status": "success",
  "stats": {
    "total_tweets": 100,
    "disaster_tweets": 45,
    "safe_tweets": 55,
    "total_clusters": 8,
    "critical_alerts": 2,
    "high_alerts": 3,
    "tweets_with_location": 30
  }
}
```

## 🎨 Frontend Components

### 1. **AlertsPanel Component**

- Displays serious disaster alerts (credibility ≥ 0.7)
- Shows: category, severity, tweet count, credibility score
- Color-coded by alert level (Critical=Red, High=Orange, etc.)
- Shows sample tweets from each cluster
- Auto-refreshes every 30 seconds

### 2. **Enhanced Map Component**

- Shows clusters as colored circles on map
- Circle radius scales with tweet count
- Color indicates alert level
- Toggle to show/hide clusters
- Click cluster to see details (credibility, tweet count, etc.)

## 🔧 Setup & Installation

### 1. Install Dependencies

```bash
cd backend
pip install sqlalchemy scipy
```

### 2. Database Initialization

The database is automatically initialized when the server starts. The SQLite database file is created at:

```
backend/disaster_tweets.db
```

### 3. Start Server

```bash
cd backend
python run.py
```

The database will be created automatically on first run.

## 📈 How It Works

1. **User analyzes a tweet** → Tweet is saved to database
2. **If disaster with location** → Clustering is triggered
3. **Clustering algorithm**:
   - Groups tweets by category
   - Within each category, clusters by location (10km radius)
   - Calculates cluster center and credibility
4. **Alert generation**:
   - High credibility clusters (≥0.7) appear in AlertsPanel
   - Critical alerts (≥0.8, 5+ tweets, High severity) are highlighted
5. **Visualization**:
   - Clusters shown as circles on map
   - Individual tweets shown as markers
   - Alerts shown in dedicated panel

## 🎯 Use Cases

### Example Scenario:

1. User 1: "Massive flood in New York, NY! Streets are flooded!"
2. User 2: "Flooding in Manhattan, New York. Water everywhere!"
3. User 3: "Serious flood in NYC, multiple areas affected"
4. User 4: "Flood in New York City, emergency services responding"
5. User 5: "Major flooding in New York, NY area"

**Result:**

- All 5 tweets cluster together (same location, same category)
- Credibility score: ~0.85 (high)
- Alert level: **Critical** (5 tweets, high credibility, flood category)
- Alert appears in AlertsPanel with red "Critical" badge
- Large red circle on map showing cluster area

## 🔍 Credibility Calculation Example

For a cluster with 5 flood tweets in New York:

- **Count Score**: log10(5) × 0.3 + 0.2 = ~0.41
- **Consistency**: 1.0 (all "Flood")
- **Avg Confidence**: 0.90 (high confidence)
- **Severity**: High (multiplier 1.2)

**Final Credibility**: (0.41 × 0.4 + 1.0 × 0.2 + 0.90 × 0.4) × 1.0 = **0.844** (84.4%)

## 🚀 Future Enhancements

- Time-based clustering (recent tweets weighted higher)
- Machine learning for credibility prediction
- Email/SMS alerts for critical disasters
- Historical trend analysis
- Multi-language support
- Integration with external disaster databases

---

**The clustering system provides intelligent aggregation of disaster reports, helping identify serious situations where multiple people report the same disaster in the same area!** 🎯
