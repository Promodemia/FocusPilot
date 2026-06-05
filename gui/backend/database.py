import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import json

DB_PATH = Path(__file__).parent / "focuspilot.db"


class Database:
    def __init__(self):
        self.db_path = DB_PATH
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_plan (
                    id INTEGER PRIMARY KEY,
                    date TEXT UNIQUE,
                    plan_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS training_data (
                    id INTEGER PRIMARY KEY,
                    timestamp TIMESTAMP,
                    app_name TEXT,
                    category TEXT,
                    features JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id INTEGER PRIMARY KEY,
                    date TEXT UNIQUE,
                    work_time INTEGER DEFAULT 0,
                    distraction_time INTEGER DEFAULT 0,
                    communication_time INTEGER DEFAULT 0,
                    break_time INTEGER DEFAULT 0,
                    plan_adherence REAL DEFAULT 0.0
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback_log (
                    id INTEGER PRIMARY KEY,
                    timestamp TIMESTAMP,
                    event_type TEXT,
                    action TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def save_plan(self, date: str, plan_text: str) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO daily_plan (date, plan_text) VALUES (?, ?)",
                    (date, plan_text)
                )
                conn.commit()
            return True
        except Exception as e:
            print(f"Error saving plan: {e}")
            return False

    def get_plan(self, date: str) -> Optional[str]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT plan_text FROM daily_plan WHERE date = ?", (date,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception:
            return None

    def add_training_sample(self, timestamp: str, app_name: str, category: str, features: Dict) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO training_data (timestamp, app_name, category, features) VALUES (?, ?, ?, ?)",
                    (timestamp, app_name, category, json.dumps(features))
                )
                conn.commit()
            return True
        except Exception:
            return False

    def get_training_data(self) -> List[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT timestamp, app_name, category, features FROM training_data ORDER BY timestamp DESC LIMIT 1000")
                rows = cursor.fetchall()
                return [
                    {
                        "timestamp": row[0],
                        "app_name": row[1],
                        "category": row[2],
                        "features": json.loads(row[3]) if row[3] else {}
                    }
                    for row in rows
                ]
        except Exception:
            return []

    def save_stats(self, date: str, stats: Dict[str, Any]) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT OR REPLACE INTO daily_stats 
                       (date, work_time, distraction_time, communication_time, break_time, plan_adherence)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (date, stats.get("work_time", 0), stats.get("distraction_time", 0),
                     stats.get("communication_time", 0), stats.get("break_time", 0),
                     stats.get("plan_adherence", 0.0))
                )
                conn.commit()
            return True
        except Exception:
            return False

    def get_stats(self, date: str) -> Optional[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT work_time, distraction_time, communication_time, break_time, plan_adherence FROM daily_stats WHERE date = ?",
                    (date,)
                )
                result = cursor.fetchone()
                if result:
                    return {
                        "work_time": result[0],
                        "distraction_time": result[1],
                        "communication_time": result[2],
                        "break_time": result[3],
                        "plan_adherence": result[4]
                    }
                return None
        except Exception:
            return None

    def add_feedback(self, event_type: str, action: str) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO feedback_log (timestamp, event_type, action) VALUES (?, ?, ?)",
                    (datetime.utcnow().isoformat(), event_type, action)
                )
                conn.commit()
            return True
        except Exception:
            return False
