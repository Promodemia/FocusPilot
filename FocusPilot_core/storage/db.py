"""
Database Manager
SQLite база данных для хранения плана, обучающих данных и обратной связи
"""

import logging
import sqlite3
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import os

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Менеджер базы данных SQLite"""
    
    def __init__(self, db_path: str = "focuspilot.db"):
        """
        Инициализация менеджера базы данных
        
        Args:
            db_path: путь к файлу БД
        """
        self.db_path = db_path
        self.init_database()
    
    def init_database(self) -> None:
        """Инициализация схемы БД"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Таблица дневного плана
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS daily_plan (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL UNIQUE,
                        plan_text TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Таблица обучающих данных
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS training_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TIMESTAMP NOT NULL,
                        app_name TEXT,
                        window_title TEXT,
                        url TEXT,
                        category TEXT NOT NULL,
                        features JSON,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Таблица логов обратной связи
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS feedback_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TIMESTAMP NOT NULL,
                        event_type TEXT,
                        category TEXT,
                        action TEXT,
                        user_feedback TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Таблица метаданных модели
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS model_metadata (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        key TEXT NOT NULL UNIQUE,
                        value TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Таблица статистики
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS daily_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL UNIQUE,
                        work_time INTEGER,
                        communication_time INTEGER,
                        distraction_time INTEGER,
                        break_time INTEGER,
                        neutral_time INTEGER,
                        afk_time INTEGER,
                        plan_adherence REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
                logger.info(f"Database initialized: {self.db_path}")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def save_daily_plan(self, date: str, plan_text: str) -> bool:
        """
        Сохранение дневного плана
        
        Args:
            date: дата в формате YYYY-MM-DD
            plan_text: текст плана
            
        Returns:
            True если успешно
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO daily_plan (date, plan_text, updated_at)
                    VALUES (?, ?, ?)
                """, (date, plan_text, datetime.utcnow().isoformat()))
                conn.commit()
                logger.info(f"Daily plan saved for {date}")
                return True
        except Exception as e:
            logger.error(f"Error saving daily plan: {e}")
            return False
    
    def get_daily_plan(self, date: str) -> Optional[str]:
        """
        Получение дневного плана
        
        Args:
            date: дата в формате YYYY-MM-DD
            
        Returns:
            Текст плана или None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT plan_text FROM daily_plan WHERE date = ?", (date,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting daily plan: {e}")
            return None
    
    def add_training_sample(
        self,
        timestamp: datetime,
        app_name: str,
        window_title: str,
        url: str,
        category: str,
        features: Dict[str, Any]
    ) -> bool:
        """
        Добавление обучающего примера
        
        Args:
            timestamp: время события
            app_name: имя приложения
            window_title: заголовок окна
            url: URL
            category: категория активности
            features: словарь признаков
            
        Returns:
            True если успешно
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO training_data 
                    (timestamp, app_name, window_title, url, category, features)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    timestamp.isoformat(),
                    app_name,
                    window_title,
                    url,
                    category,
                    json.dumps(features)
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding training sample: {e}")
            return False
    
    def get_training_samples(self, limit: int = 10000) -> List[Dict[str, Any]]:
        """
        Получение обучающих примеров
        
        Args:
            limit: максимальное количество примеров
            
        Returns:
            Список примеров
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT timestamp, app_name, window_title, url, category, features
                    FROM training_data
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
                
                samples = []
                for row in cursor.fetchall():
                    features = json.loads(row[5]) if row[5] else {}
                    samples.append({
                        "timestamp": row[0],
                        "app_name": row[1],
                        "window_title": row[2],
                        "url": row[3],
                        "label": row[4],
                        "features": features
                    })
                
                return samples
        except Exception as e:
            logger.error(f"Error getting training samples: {e}")
            return []
    
    def add_feedback(
        self,
        timestamp: datetime,
        event_type: str,
        category: str,
        action: str,
        user_feedback: Optional[str] = None
    ) -> bool:
        """
        Добавление логов обратной связи пользователя
        
        Args:
            timestamp: время события
            event_type: тип события (distraction_notification, etc)
            category: категория активности
            action: действие пользователя (return, ignore, etc)
            user_feedback: дополнительный комментарий
            
        Returns:
            True если успешно
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO feedback_log 
                    (timestamp, event_type, category, action, user_feedback)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    timestamp.isoformat(),
                    event_type,
                    category,
                    action,
                    user_feedback
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding feedback: {e}")
            return False
    
    def update_model_metadata(self, metadata: Dict[str, Any]) -> bool:
        """
        Обновление метаданных модели
        
        Args:
            metadata: словарь с метаданными
            
        Returns:
            True если успешно
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for key, value in metadata.items():
                    value_str = json.dumps(value) if not isinstance(value, str) else value
                    cursor.execute("""
                        INSERT OR REPLACE INTO model_metadata (key, value, updated_at)
                        VALUES (?, ?, ?)
                    """, (key, value_str, datetime.utcnow().isoformat()))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating model metadata: {e}")
            return False
    
    def get_model_metadata(self, key: str) -> Optional[Any]:
        """
        Получение метаданных модели
        
        Args:
            key: ключ метаданных
            
        Returns:
            Значение или None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM model_metadata WHERE key = ?", (key,))
                result = cursor.fetchone()
                if result:
                    try:
                        return json.loads(result[0])
                    except:
                        return result[0]
                return None
        except Exception as e:
            logger.error(f"Error getting model metadata: {e}")
            return None
    
    def save_daily_stats(self, date: str, stats: Dict[str, Any]) -> bool:
        """
        Сохранение суточной статистики
        
        Args:
            date: дата в формате YYYY-MM-DD
            stats: словарь статистики
            
        Returns:
            True если успешно
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO daily_stats
                    (date, work_time, communication_time, distraction_time, 
                     break_time, neutral_time, afk_time, plan_adherence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    date,
                    stats.get("work_time", 0),
                    stats.get("communication_time", 0),
                    stats.get("distraction_time", 0),
                    stats.get("break_time", 0),
                    stats.get("neutral_time", 0),
                    stats.get("afk_time", 0),
                    stats.get("plan_adherence", 0.0),
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving daily stats: {e}")
            return False
    
    def get_daily_stats(self, date: str) -> Optional[Dict[str, Any]]:
        """
        Получение суточной статистики
        
        Args:
            date: дата в формате YYYY-MM-DD
            
        Returns:
            Словарь статистики или None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT work_time, communication_time, distraction_time,
                           break_time, neutral_time, afk_time, plan_adherence
                    FROM daily_stats WHERE date = ?
                """, (date,))
                
                result = cursor.fetchone()
                if result:
                    return {
                        "work_time": result[0],
                        "communication_time": result[1],
                        "distraction_time": result[2],
                        "break_time": result[3],
                        "neutral_time": result[4],
                        "afk_time": result[5],
                        "plan_adherence": result[6],
                    }
                return None
        except Exception as e:
            logger.error(f"Error getting daily stats: {e}")
            return None
    
    def get_recent_feedback(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Получение недавних логов обратной связи
        
        Args:
            limit: максимальное количество
            
        Returns:
            Список логов
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT timestamp, event_type, category, action, user_feedback
                    FROM feedback_log
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
                
                feedback = []
                for row in cursor.fetchall():
                    feedback.append({
                        "timestamp": row[0],
                        "event_type": row[1],
                        "category": row[2],
                        "action": row[3],
                        "user_feedback": row[4],
                    })
                
                return feedback
        except Exception as e:
            logger.error(f"Error getting feedback: {e}")
            return []
