# 🚨 AI Disaster Intelligence System

A **production-ready, advanced-level** NLP project for disaster tweet classification with geotagging, featuring model comparison, hyperparameter tuning, and comprehensive evaluation.

## ✨ Features

### 🎯 Core Capabilities

- **Multi-Model Comparison**: Automatically trains and compares DistilBERT, BERT, and RoBERTa
- **Hyperparameter Tuning**: Grid search and random search for optimal parameters
- **Advanced Evaluation**: Comprehensive metrics (Accuracy, F1, Precision, Recall, ROC-AUC)
- **Early Stopping**: Prevents overfitting with configurable patience
- **Model Checkpointing**: Saves training progress for resuming
- **Automatic Best Model Selection**: Selects and deploys the best performing model
- **One-Time Training**: Models trained once, cached for future use
- **Smart Model Loading**: API automatically finds and loads best model

### 📊 Model Training Features

- Multiple transformer architectures (DistilBERT, BERT, RoBERTa)
- Configurable hyperparameters
- Gradient accumulation and clipping
- Learning rate scheduling with warmup
- Stratified train/validation/test splits
- Comprehensive data preprocessing pipeline

### 🗺️ Geotagging & Visualization

- Location extraction using spaCy NER
- Geocoding with GeoPy (OpenStreetMap)
- Interactive map visualization (Leaflet)
- Real-time analytics dashboard
- Professional UI with advanced labels

## 🚀 Quick Start

**📖 For detailed instructions, see: [`START_HERE.md`](START_HERE.md)**

### Prerequisites

- **Python 3.8 - 3.13** (Python 3.12 recommended, **Python 3.14 NOT supported** - PyTorch doesn't support it yet)
- Node.js 14+ and npm
- Internet connection

**⚠️ Important:** If you have Python 3.14, you need to use Python 3.12. See `PYTHON_VERSION_WARNING.md` for details.

### Quick Start (2 Commands)

**Terminal 1 - Backend:**

```powershell
cd backend
python run.py
```

**Terminal 2 - Frontend:**

```powershell
cd frontend/disaster-frontend
npm run dev
```

**Then open:** http://localhost:3000

---

## � Merged Documentation

> The following documentation sections were merged from individual `.md` files into this single canonical `README.md` file. The original files have been deprecated and now redirect here.

### 🚀 Start Here (Quick Guide)

- Start backend:

```powershell
cd backend
python run.py
```

- Start frontend (new terminal):

```powershell
cd frontend/disaster-frontend
npm run dev
```

Open `http://localhost:3000` and enter a tweet to analyze.

---

### ⚠️ Python Version Warning

- PyTorch supports Python 3.8 - 3.13. Python 3.14 is not supported.
- Recommended: use Python 3.12. Create a new venv using Python 3.12 and reinstall requirements.

---

### 💾 Persistence & Data Loading

- All analyzed tweets are persisted to SQLite (`backend/disaster_tweets.db`).
- The app loads recent tweets on startup and the frontend loads historical data on refresh (last 100 tweets by default).
- API: `GET /tweets?limit=100&disaster_only=false`.

---

### 🎯 Clustering & Alerts (Overview)

- Tweets are clustered by proximity (approx. 10 km) and category.
- Credibility is computed from count, consistency, average confidence, and severity.
- Alert levels: Critical, High, Medium, Low. API endpoints include `/clusters` and `/alerts`.

---

### 🎨 UI Improvements (Highlights)

- Modern design system, glassmorphism, Inter font, improved UX (skeleton loaders, micro-interactions), responsive and production-ready.
- Map and analytics UI enhancements are included in the frontend.

---

### 🔑 API Keys (Optional Enhancements)

- Project works without API keys using OpenStreetMap and Nominatim.
- Optional integrations: Mapbox/Google Maps tiles, Google/Mapbox geocoding, OpenWeatherMap, Twitter API. Use environment variables or `.env`.

---

### 📁 Project Structure (Summary)

- `backend/` - Flask API, training scripts, model artifacts in `models/`, database `disaster_tweets.db`.
- `frontend/disaster-frontend/` - React + Vite app with components for form, results, map, analytics.
- See the top of this README for full setup and usage sections.

---

## �📖 Detailed Setup

### Step 1: Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment (if not exists)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

### Step 2: Download Dataset

1. Download `train.csv` from [Kaggle "Real or Not? Disaster Tweets"](https://www.kaggle.com/c/nlp-getting-started/data)
2. Place it in the `backend/` directory

### Step 3: Train Models (One Time Only)

```bash
# Make sure you're in backend/ with venv activated
python train_advanced.py
```

**What happens:**

- Trains DistilBERT, BERT, and RoBERTa
- Compares all models
- Selects best one automatically
- Saves to `models/best_model/`
- Takes 10-30 minutes (depending on hardware)

**If models already exist:**

```
✅ MODELS ALREADY TRAINED
Best model found at: models/best_model
To retrain: python train_advanced.py --force
```

### Step 4: Start Backend API

**Simple Method (Recommended):**

```powershell
cd backend
python run.py
```

That's it! The `run.py` script automatically finds and uses the virtual environment.

**Alternative Methods:**

**Option 2: Manual Activation**

```powershell
cd backend
.\venv\Scripts\Activate.ps1  # Activate venv
python app.py                 # Then run
```

**Option 3: Helper Script**

```powershell
cd backend
.\START_SERVER.ps1
```

**Linux/Mac:**

```bash
cd backend
python run.py  # Or: source venv/bin/activate && python app.py
```

**What happens:**

- ✅ Auto-loads best model
- ✅ Displays model information
- ✅ Runs on `http://localhost:5000`

**If you see errors:**

- "ModuleNotFoundError": Packages not installed → `pip install -r requirements.txt`
- "torch not found": Python 3.14 issue → See `PYTHON_VERSION_WARNING.md`
- "Model not found": Need to train → `python train_advanced.py`

### Step 5: Start Frontend

**Open a NEW terminal/PowerShell window:**

```powershell
cd frontend/disaster-frontend

# Install dependencies (first time only)
npm install

# Start Vite dev server
npm run dev
```

**The app will open at:** `http://localhost:3000`

**Note:** This project uses **Vite** for faster development and production builds. The frontend is production-ready with optimized builds.

---

## 📖 Usage

1. **Start both servers** (backend on port 5000, frontend on port 3000)
2. **Enter a tweet** in the form, for example:
   - `"Massive flood in Phagwara, Punjab. Roads are blocked!"`
   - `"Earthquake tremors felt in Delhi, magnitude 5.2"`
   - `"Fire broke out in Mumbai building, 20 injured"`
   - `"Fire at 40.7128, -74.0060"` (with coordinates)
3. **View results:**
   - Classification (Disaster/Not Disaster) with confidence
   - Category and severity
   - Risk assessment
   - Extracted location and coordinates
   - Map visualization with marker
   - Analytics charts updating in real-time

## 🔧 Advanced Features

### Model Comparison

Run `python train_advanced.py` to compare multiple models:

```
🏆 Best Model: roberta-base
   Best f1_score: 0.8215
   Accuracy: 0.8234
   ROC-AUC: 0.9123
```

### Hyperparameter Tuning

```bash
python hyperparameter_tuning.py
```

Choose:

- Random Search (faster, recommended)
- Grid Search (exhaustive, slower)

### Configuration

Edit `backend/config.py` to:

- Add/modify models
- Change hyperparameters
- Adjust training settings

## 📡 API Endpoints

### Health Check

```bash
GET http://localhost:5000/
```

### Single Prediction

```bash
POST http://localhost:5000/predict
Content-Type: application/json

{
  "text": "Massive flood in Phagwara, Punjab. Roads are blocked!"
}
```

**Response:**

```json
{
  "status": "success",
  "tweet": "...",
  "disaster_text": "🚨 Disaster Detected",
  "confidence_percentage": 95.2,
  "category": "Flood",
  "severity": "High",
  "risk_level": "Critical",
  "location": "Phagwara, Punjab, India",
  "lat": 31.2177,
  "lon": 75.7698,
  "model_info": {
    "model_name": "roberta-base",
    "accuracy": 0.8234,
    "f1_score": 0.8215
  }
}
```

### Batch Prediction

```bash
POST http://localhost:5000/batch_predict
Content-Type: application/json

{
  "tweets": ["Tweet 1", "Tweet 2", "Tweet 3"]
}
```

## 🎨 Frontend Features

- **Professional UI**: Gradient design with advanced labels
- **Real-time Visualization**: Confidence bars, risk indicators
- **Interactive Map**: Leaflet map with markers
- **Analytics Dashboard**: Real-time charts and statistics
- **Responsive Design**: Works on all screen sizes

## 🔑 Optional API Keys

The project works **perfectly without any API keys**! All features use free services:

- Maps: OpenStreetMap (free)
- Geocoding: Nominatim (free, rate-limited)

**Optional enhancements** (see `API_KEYS_GUIDE.md`):

- Mapbox/Google Maps (better map tiles)
- Google/Mapbox Geocoding (better accuracy)
- OpenWeatherMap (weather context)
- Twitter API (real-time tweets)

## 🛠️ Technologies Used

### Backend

- Python 3.8-3.13
- PyTorch & Transformers (DistilBERT, BERT, RoBERTa)
- Flask (REST API)
- spaCy (NER for locations)
- GeoPy (Geocoding)
- scikit-learn (Evaluation)

### Frontend

- React 18 with Vite (Fast build tool)
- React Leaflet (Map visualization)
- Recharts (Analytics charts)
- Modern CSS (Gradients, animations)
- Error boundaries and production optimizations

## 📊 Model Details

- **Base Models**: DistilBERT, BERT, RoBERTa
- **Input**: Preprocessed tweet text
- **Output**: Binary classification (Disaster/Not Disaster)
- **Training**: 3 epochs with validation, early stopping
- **Selection**: Best model selected based on F1-score

## 🎓 Perfect for Assessment

This project demonstrates:

- ✅ Advanced ML engineering (model comparison, hyperparameter tuning)
- ✅ Best practices (early stopping, checkpointing, logging)
- ✅ Production-ready code (modular, configurable, documented)
- ✅ Comprehensive evaluation (multiple metrics, detailed reports)
- ✅ Automation (automatic best model selection)
- ✅ Professional UI (advanced labels, modern design)
- ✅ One-time training (efficient resource usage)

## 🐛 Troubleshooting

### Backend Issues

- **Model not found**: Run `python train_advanced.py` first
- **spaCy model error**: Run `python -m spacy download en_core_web_sm`
- **Port 5000 in use**: Change port in `app.py` or kill the process
- **ModuleNotFoundError**: Activate venv or use `python run.py`

### Frontend Issues

- **Cannot connect to backend**: Make sure Flask is running on port 5000
- **npm install fails**: Delete `node_modules` and `package-lock.json`, then `npm install`
- **Map not showing**:
  - Ensure Leaflet CSS is loaded (automatically imported)
  - Check browser console for errors
  - Verify internet connection for map tiles
  - Try refreshing the page
- **Vite dev server issues**: Clear cache with `npm run dev -- --force`

### Python 3.14 Issues

- **PyTorch not found**: Use Python 3.12 instead (see `PYTHON_VERSION_WARNING.md`)
- **spaCy errors**: Use Python 3.13 or earlier

## 📝 License

Educational/Portfolio Project

## 🙏 Acknowledgments

- Dataset: [Kaggle "Real or Not? Disaster Tweets"](https://www.kaggle.com/c/nlp-getting-started/data)
- Models: Hugging Face Transformers
- Maps: OpenStreetMap contributors

---

**Built with ❤️ for advanced NLP and ML engineering**
