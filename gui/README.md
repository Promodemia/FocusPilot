# FocusPilot v2 - Architecture Rewrite

Modern desktop application with **Rust/Tauri frontend** and **Python FastAPI backend**.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FOCUSPILOT APP                            │
│              (Tauri - Rust/Tauri-ui)                         │
│  - Desktop Window + Tray                                     │
│  - Plan input, Stats display                                │
│  - Notification listener (port 3000)                        │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP REST
                     │ (FastAPI)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              FOCUSPILOT BACKEND                              │
│           (FastAPI - Python 3.10+)                          │
│  - Activity monitoring (ActivityWatch)                      │
│  - ML classification (sklearn)                              │
│  - SQLite database                                          │
│  - POST /notify to Tauri                                   │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Backend API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Backend health check (aw_available: bool) |
| POST | `/plan` | Save daily plan (text) |
| GET | `/plan` | Get today's plan |
| GET | `/current_state` | Current activity + stats |
| GET | `/stats` | Daily statistics |
| POST | `/feedback` | Log user action |
| POST | `/train` | Retrain ML models |
| POST | `/pause` | Pause/resume monitoring |
| POST | `/notify` | Notification from backend (internal) |

## 🔧 Quick Start

### Prerequisites
- **Python 3.10+**
- **Node.js 16+**
- **Rust & Cargo** (for building Tauri)
- **ActivityWatch** (optional but recommended)

### Installation

#### 1. Setup Python Backend
```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate.bat
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

#### 2. Setup Tauri Frontend
```bash
cd frontend
npm install
```

#### 3. Install Rust (if needed)
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

## 🚀 Running

### Option 1: Separate Terminals
**Terminal 1 - Backend:**
```bash
cd FocusPilot-v2
.\start_backend.bat  # Windows
# or: python backend/main.py
```

**Terminal 2 - Frontend:**
```bash
cd FocusPilot-v2
.\start_frontend.bat  # Windows
# or: cd frontend && npm run tauri:dev
```

### Option 2: Double-Click (Windows)
1. Double-click `start_backend.bat` (runs in background)
2. Double-click `start_frontend.bat` (launches Tauri dev window)

## 📁 Project Structure

```
FocusPilot-v2/
├── backend/
│   ├── main.py              # FastAPI server
│   ├── database.py          # SQLite layer
│   ├── models.py            # ML classification
│   ├── monitor.py           # Activity monitoring
│   ├── requirements.txt      # Python dependencies
│   └── focuspilot.db        # (created on first run)
│
├── frontend/
│   ├── src-tauri/
│   │   ├── src/
│   │   │   ├── main.rs      # Tauri entry
│   │   │   ├── commands.rs  # Tauri commands
│   │   │   ├── backend.rs   # Backend utils
│   │   │   └── lib.rs
│   │   ├── Cargo.toml
│   │   └── tauri.conf.json
│   │
│   ├── index.html           # Main UI
│   ├── vite.config.js
│   ├── package.json
│   └── node_modules/ (created on npm install)
│
├── start_backend.bat
├── start_frontend.bat
└── README.md
```

## 🎯 Features

### ✅ Implemented
- **Activity Monitoring**: Polls ActivityWatch every 2 seconds
- **ML Classification**: Random Forest for work/communication/distraction
- **Daily Plans**: Save and manage daily goals
- **Statistics**: Track time spent in each category
- **Notifications**: Real-time alerts for distractions
- **Pause Controls**: Temporarily disable monitoring
- **Tray Menu**: Quick access via system tray
- **Auto-Launch Backend**: Tauri checks health and launches Python if needed

### 🔄 Monitor Loop (Backend)
```
Every 2 seconds:
1. Get current activity from ActivityWatch
2. Extract features (app_name, window_title, etc.)
3. Classify with ML model → category, confidence
4. Update daily statistics
5. Check thresholds:
   - Distraction > 2 minutes? → Send notification
   - Distraction probability > 0.7? → Send alert
6. Store in database
```

## 🔌 Communication Flow

1. **Tauri Frontend** starts, checks `/health` endpoint
2. If backend unavailable, auto-launches `python backend/main.py`
3. **Backend** connects to ActivityWatch on startup
4. **Backend** spawns monitoring thread (async loop)
5. Every 2 seconds:
   - Monitoring thread checks activity
   - If threshold met → POST to `http://localhost:3000/notify`
6. **Tauri** listens on port 3000 for notifications
7. Notifications appear as system toasts

## 📊 Database Schema

### daily_plan
```sql
id, date (UNIQUE), plan_text, created_at
```

### training_data
```sql
id, timestamp, app_name, category, features (JSON), created_at
```

### daily_stats
```sql
id, date (UNIQUE), work_time, distraction_time, 
communication_time, break_time, plan_adherence
```

### feedback_log
```sql
id, timestamp, event_type, action, created_at
```

## ⚙️ Configuration

### Backend (main.py)
- **Backend Port**: 8765
- **Monitor Interval**: 2 seconds
- **Distraction Threshold**: 2 minutes or 0.7 probability
- **Database**: `backend/focuspilot.db`

### Frontend (Tauri)
- **Notification Port**: 3000
- **Window Size**: 900x700 (resizable)
- **Tray Menu**: Show/Pause/Quit

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check Python
python --version

# Check dependencies
cd backend
pip install -r requirements.txt

# Check ActivityWatch
# Open http://localhost:5600 in browser
```

### Tauri won't build
```bash
# Install Rust
rustup update

# Clear cache
cd frontend
cargo clean
rm -rf node_modules
npm install
```

### No notifications appearing
```bash
# Check backend health
curl http://localhost:8765/health

# Check logs
tail -f backend.log
```

## 📝 Logs

- **Backend**: `backend/backend.log`
- **Frontend**: Browser console (F12)

## 🤖 ML Models

- **Classifier**: `backend/model.pkl` (RandomForest)
- **Predictor**: `backend/predictor.pkl` (TimeSeriesForest)
- **Fallback**: Rule-based classification if models not available

## 🔐 Security Notes

- Backend runs on `localhost` only
- No authentication (local use only)
- CORS disabled (Tauri communicates locally)
- Database file has no encryption (consider adding)

## 🚀 Building for Release

```bash
# Backend
python -m PyInstaller --onefile backend/main.py

# Frontend
cd frontend
npm run tauri:build
```

## 📄 License

MIT - Feel free to modify and distribute

## 🤝 Contributing

Issues and PRs welcome!

---

**FocusPilot v2** - Stay Focused, Track Progress 🎯
