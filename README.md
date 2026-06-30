# FocusPilot v2

> Desktop productivity app with ML activity classification. Python FastAPI + Rust/Tauri.

Десктопное приложение для отслеживания продуктивности с ML-классификацией активности в реальном времени. Бэкенд на Python FastAPI, фронтенд на Rust/Tauri.

---

## 🎯 Demo

![FocusPilot Tray](docs/demo_tray.png)
<!-- Добавь скриншот окна приложения или GIF с работой трея и нотификаций -->

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FOCUSPILOT APP                           │
│              (Tauri - Rust/Tauri-ui)                        │
│  - Desktop Window + Tray                                    │
│  - Plan input, Stats display                                │
│  - Notification listener (port 3000)                        │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP REST (FastAPI)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              FOCUSPILOT BACKEND                             │
│           (FastAPI - Python 3.10+)                          │
│  - Activity monitoring (ActivityWatch)                      │
│  - ML classification (sklearn RandomForest)                 │
│  - SQLite database                                          │
│  - POST /notify to Tauri                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🤖 ML Model Details

**Classifier:** `RandomForestClassifier` (scikit-learn)

**Input features:**
| Feature | Description |
|---|---|
| `app_name` | Name of active application (encoded) |
| `window_title` | Window title keywords (TF-IDF tokens) |
| `hour_of_day` | Hour (0–23) |
| `day_of_week` | Day (0=Mon … 6=Sun) |
| `duration_seconds` | Time spent on current window |

**Output classes:**
- `work` — productive activity (IDE, docs, terminals)
- `communication` — Slack, email, Telegram
- `distraction` — social media, video, games
- `break` — system idle / screensaver

**Thresholds:**
- Distraction alert if `distraction_time > 2 min` OR `distraction_probability > 0.7`

**Fallback:** Rule-based classification if model file not available.

---

## 📋 Backend API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check (aw_available: bool) |
| POST | `/plan` | Save daily plan (text) |
| GET | `/plan` | Get today's plan |
| GET | `/current_state` | Current activity + stats |
| GET | `/stats` | Daily statistics |
| POST | `/feedback` | Log user action |
| POST | `/train` | Retrain ML models |
| POST | `/pause` | Pause/resume monitoring |

---

## 🔧 Quick Start

### Prerequisites
- **Python 3.10+**
- **Node.js 16+**
- **Rust & Cargo**
- **ActivityWatch** (optional but recommended)

### Installation

```bash
# 1. Backend
cd FocusPilot_core
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate.bat     # Windows
pip install -r requirements.txt

# 2. Frontend
cd gui
npm install

# 3. Rust (if needed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### Running

**Terminal 1 — Backend:**
```bash
python FocusPilot_core/main.py
```

**Terminal 2 — Frontend:**
```bash
cd gui && npm run tauri:dev
```

---

## 📁 Project Structure

```
FocusPilot/
├── FocusPilot_core/
│   ├── main.py              # FastAPI server
│   ├── database.py          # SQLite layer
│   ├── models.py            # ML classification
│   ├── monitor.py           # Activity monitoring
│   └── requirements.txt
├── gui/
│   ├── src-tauri/
│   │   ├── src/main.rs
│   │   ├── src/commands.rs
│   │   └── tauri.conf.json
│   ├── index.html
│   └── package.json
├── .gitignore               # ← includes *.log, *.db, venv/
├── CONTRIBUTING.md
└── README.md
```

---

## 📊 Database Schema

```sql
-- Daily plans
CREATE TABLE daily_plan (
    id INTEGER PRIMARY KEY,
    date TEXT UNIQUE,
    plan_text TEXT,
    created_at TEXT
);

-- ML training data
CREATE TABLE training_data (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    app_name TEXT,
    category TEXT,
    features TEXT,   -- JSON
    created_at TEXT
);

-- Daily statistics
CREATE TABLE daily_stats (
    id INTEGER PRIMARY KEY,
    date TEXT UNIQUE,
    work_time INTEGER,
    distraction_time INTEGER,
    communication_time INTEGER,
    break_time INTEGER,
    plan_adherence REAL
);

-- Feedback log
CREATE TABLE feedback_log (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    event_type TEXT,
    action TEXT,
    created_at TEXT
);
```

---

## ⚙️ Configuration

| Setting | Default | Location |
|---|---|---|
| Backend port | 8765 | `main.py` |
| Notification port | 3000 | `tauri.conf.json` |
| Monitor interval | 2 sec | `monitor.py` |
| Distraction threshold | 2 min / 0.7 prob | `monitor.py` |
| Window size | 900×700 | `tauri.conf.json` |

---

## ⚠️ Known Limitations

- **No authentication** — backend runs on localhost only, not suitable for network exposure
- **ActivityWatch required** for full monitoring (app falls back to rule-based if unavailable)
- **Windows-first** — `.bat` launch scripts; macOS/Linux need manual start
- **No database encryption** — `focuspilot.db` is stored in plaintext
- **ML model cold start** — classification degrades until enough `training_data` is collected (≥50 samples recommended)
- **Single-user only** — no multi-profile support

---

## 🐛 Troubleshooting

```bash
# Backend won't start
python --version          # must be 3.10+
pip install -r requirements.txt

# Check ActivityWatch
curl http://localhost:5600/api/0/info

# No notifications
curl http://localhost:8765/health

# Tauri build fails
rustup update
cd gui && cargo clean && rm -rf node_modules && npm install
```

Logs:
- **Backend:** `backend/backend.log`
- **Frontend:** Browser console (F12)

---

## 🚀 Building for Release

```bash
# Backend → single executable
python -m PyInstaller --onefile FocusPilot_core/main.py

# Frontend → installer
cd gui && npm run tauri:build
```

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, coding style, and how to run tests.

Issues and PRs welcome!

---

## 📄 License

MIT — feel free to modify and distribute.

---

**FocusPilot v2** — Stay Focused, Track Progress 🎯
