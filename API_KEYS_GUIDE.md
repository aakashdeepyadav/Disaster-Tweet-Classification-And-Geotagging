# ⚠️ DEPRECATED — Moved to `README.md`

This guide has been merged into `README.md` under "Merged Documentation → API Keys (Optional)".

**Please consult `README.md` for optional API integrations and instructions.**

## ✅ Current Status: **No API Keys Required!**

The project works **perfectly** without any API keys. Everything is functional with free services:

- ✅ **Maps**: OpenStreetMap (free, no key needed)
- ✅ **Geocoding**: Nominatim/OpenStreetMap (free, rate-limited but sufficient)
- ✅ **All features work out of the box**

## 🚀 Optional Enhancements (If You Want Better Features)

You can add API keys to enable enhanced features. All are **completely optional**.

### 1. **Map Services** (Better Map Tiles)

#### Option A: Mapbox (Recommended)

- **Why**: Beautiful, fast map tiles
- **Free Tier**: 50,000 map loads/month
- **Get Key**: https://account.mapbox.com/access-tokens/
- **Set**: `MAPBOX_ACCESS_TOKEN=your_key_here`

#### Option B: Google Maps

- **Why**: Familiar, detailed maps
- **Free Tier**: $200 credit/month
- **Get Key**: https://console.cloud.google.com/google/maps-apis
- **Set**: `GOOGLE_MAPS_API_KEY=your_key_here`

### 2. **Geocoding Services** (Better Location Accuracy)

#### Option A: Google Geocoding API

- **Why**: Most accurate, handles ambiguous locations
- **Free Tier**: $200 credit/month
- **Get Key**: https://console.cloud.google.com/google/maps-apis
- **Set**: `GOOGLE_GEOCODING_API_KEY=your_key_here`

#### Option B: Mapbox Geocoding

- **Why**: Fast, good accuracy
- **Free Tier**: 100,000 requests/month
- **Get Key**: https://account.mapbox.com/access-tokens/
- **Set**: `MAPBOX_GEOCODING_TOKEN=your_key_here`

### 3. **Weather API** (Weather Context)

#### OpenWeatherMap

- **Why**: Add weather context to disaster analysis
- **Free Tier**: 1,000 calls/day
- **Get Key**: https://openweathermap.org/api
- **Set**: `OPENWEATHER_API_KEY=your_key_here`
- **Feature**: Shows weather conditions at disaster location

### 4. **Twitter API** (Real-time Tweets)

#### Twitter API v2

- **Why**: Fetch real-time disaster tweets
- **Free Tier**: 1,500 tweets/month
- **Get Key**: https://developer.twitter.com/
- **Set**: `TWITTER_BEARER_TOKEN=your_key_here`
- **Feature**: Real-time tweet monitoring

## 📝 How to Add API Keys

### Method 1: Environment Variables (Recommended)

**Windows (PowerShell):**

```powershell
$env:MAPBOX_ACCESS_TOKEN="your_key_here"
$env:GOOGLE_GEOCODING_API_KEY="your_key_here"
```

**Windows (Command Prompt):**

```cmd
set MAPBOX_ACCESS_TOKEN=your_key_here
set GOOGLE_GEOCODING_API_KEY=your_key_here
```

**Linux/Mac:**

```bash
export MAPBOX_ACCESS_TOKEN="your_key_here"
export GOOGLE_GEOCODING_API_KEY="your_key_here"
```

### Method 2: Create `.env` File

Create `backend/.env`:

```env
MAPBOX_ACCESS_TOKEN=your_key_here
GOOGLE_GEOCODING_API_KEY=your_key_here
OPENWEATHER_API_KEY=your_key_here
TWITTER_BEARER_TOKEN=your_key_here
```

Then install python-dotenv:

```bash
pip install python-dotenv
```

And load in `app.py`:

```python
from dotenv import load_dotenv
load_dotenv()
```

## 🎯 What Each API Enhances

### Mapbox/Google Maps

- **Current**: OpenStreetMap tiles (works great!)
- **Enhanced**: More detailed, faster loading, better styling
- **Impact**: Visual improvement only

### Google/Mapbox Geocoding

- **Current**: Nominatim (works, but rate-limited)
- **Enhanced**: Better accuracy, handles ambiguous locations
- **Impact**: More accurate coordinates

### Weather API

- **Current**: No weather data
- **Enhanced**: Shows weather conditions at disaster location
- **Impact**: Adds context (e.g., "Heavy rain during flood")

### Twitter API

- **Current**: Manual tweet input
- **Enhanced**: Real-time tweet fetching and monitoring
- **Impact**: Live disaster detection

## 💡 Recommendations

### For Assessment/Portfolio:

- **No API keys needed** - Everything works perfectly!
- Current setup is professional and complete

### For Production/Enhanced Demo:

1. **Mapbox** (free tier is generous)
2. **Google Geocoding** (most accurate)
3. **OpenWeatherMap** (adds nice context)

### For Real-time Monitoring:

- **Twitter API** (if you want live tweet fetching)

## 🔒 Security Notes

- **Never commit API keys to Git!**
- Use `.env` file and add to `.gitignore`
- Use environment variables in production
- Rotate keys if exposed

## ✅ Current Setup (No Keys Needed)

The project is **production-ready** without any API keys:

- ✅ Beautiful maps (OpenStreetMap)
- ✅ Accurate geocoding (Nominatim)
- ✅ All features functional
- ✅ Professional UI
- ✅ Complete functionality

**You don't need to add any API keys unless you want specific enhancements!**

## 📞 If You Want to Add APIs

Just let me know which APIs you want to add, and I'll:

1. Update the code to use them
2. Add the integration
3. Keep fallback to free services
4. Document the changes

**Everything works great as-is!** 🚀
