"""
Feature Extractor
Построение векторов признаков из событий ActivityWatch
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from collections import Counter
import re

logger = logging.getLogger(__name__)

# Словарь для категоризации приложений (rule-based)
CATEGORY_KEYWORDS = {
    "work": {
        "apps": ["code", "vscode", "pycharm", "idea", "visual studio", "sublime", 
                "notepad++", "sublime", "atom", "cursor", "jetbrains", "rider"],
        "urls": ["github.com", "stackoverflow.com", "docs.python.org", "devdocs",
                "jira", "confluence", "gitlab", "bitbucket", "google.com/search?", "man."],
    },
    "communication": {
        "apps": ["slack", "teams", "discord", "telegram", "mail", "outlook", 
                "thunderbird", "skype", "zoom", "whatsapp"],
        "urls": ["slack.com", "teams.microsoft.com", "discord.com", "telegram.org",
                "gmail.com", "outlook.live.com", "zoom.us"],
    },
    "distraction": {
        "apps": ["youtube", "tiktok", "instagram", "facebook", "twitter", "reddit",
                "twitch", "netflix", "spotify", "steam", "minecraft"],
        "urls": ["youtube.com", "tiktok.com", "instagram.com", "facebook.com", 
                "reddit.com", "twitter.com", "twitch.tv", "netflix.com"],
    },
    "break": {
        "apps": ["media player", "vlc", "foobar", "winamp"],
        "urls": ["youtube.com/watch", "spotify.com"],
    }
}

DISTRACTION_KEYWORDS = ["youtube", "tiktok", "reddit", "instagram", "facebook", 
                         "twitter", "netflix", "twitch", "gaming", "games"]


class FeatureExtractor:
    """Экстрактор признаков из событий ActivityWatch"""
    
    def __init__(self):
        """Инициализация экстрактора"""
        self.last_app = None
        self.focus_start_time = None
        self.app_switch_times = []
        self.active_duration = 0
        self.afk_percentage = 0
    
    def extract_features_from_events(
        self,
        events: Dict[str, List[Dict[str, Any]]],
        current_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Извлечение признаков из событий AW

        Args:
            events: словарь с событиями от AW
            current_time: текущее время (для тестирования)
            
        Returns:
            Словарь с признаками
        """
        if current_time is None:
            current_time = datetime.utcnow()
        
        window_events = events.get("window_events", [])
        url_events = events.get("url_events", [])
        afk_events = events.get("afk_events", [])
        
        features = {
            "timestamp": current_time.isoformat(),
            "app_name": self._extract_app_name(window_events),
            "window_title": self._extract_window_title(window_events),
            "url": self._extract_url(url_events),
            "hour_of_day": current_time.hour,
            "day_of_week": current_time.weekday(),
            "focus_duration": self._calculate_focus_duration(window_events),
            "switch_frequency": self._calculate_switch_frequency(window_events),
            "afk_percentage": self._calculate_afk_percentage(afk_events),
            "is_afk": self._is_afk(afk_events),
        }
        
        return features
    
    def _extract_app_name(self, window_events: List[Dict[str, Any]]) -> str:
        """Извлечение имени текущего приложения"""
        if not window_events:
            return "unknown"
        
        # Берем последнее событие
        latest = window_events[-1] if isinstance(window_events, list) else window_events
        if isinstance(latest, dict) and "data" in latest:
            app = latest["data"].get("app", "unknown")
            return app.lower() if app else "unknown"
        
        return "unknown"
    
    def _extract_window_title(self, window_events: List[Dict[str, Any]]) -> str:
        """Извлечение заголовка текущего окна"""
        if not window_events:
            return ""
        
        latest = window_events[-1] if isinstance(window_events, list) else window_events
        if isinstance(latest, dict) and "data" in latest:
            title = latest["data"].get("title", "")
            return title if title else ""
        
        return ""
    
    def _extract_url(self, url_events: List[Dict[str, Any]]) -> str:
        """Извлечение текущего URL"""
        if not url_events:
            return ""
        
        latest = url_events[-1] if isinstance(url_events, list) else url_events
        if isinstance(latest, dict) and "data" in latest:
            url = latest["data"].get("url", "")
            return url if url else ""
        
        return ""
    
    def _calculate_focus_duration(self, window_events: List[Dict[str, Any]]) -> float:
        """Расчет длительности текущего фокуса в секундах"""
        if not window_events or len(window_events) < 2:
            return 0.0
        
        try:
            # Суммируем длительности событий за последние 15 сек
            total_duration = 0
            for event in window_events:
                if isinstance(event, dict) and "duration" in event:
                    total_duration += event["duration"]
            
            return total_duration
        except Exception as e:
            logger.debug(f"Error calculating focus duration: {e}")
            return 0.0
    
    def _calculate_switch_frequency(self, window_events: List[Dict[str, Any]]) -> float:
        """Расчет частоты переключений между приложениями (per minute)"""
        if not window_events:
            return 0.0
        
        try:
            # Подсчет количества уникальных приложений за период
            apps = []
            for event in window_events:
                if isinstance(event, dict) and "data" in event:
                    app = event["data"].get("app", "unknown")
                    apps.append(app)
            
            if len(apps) <= 1:
                return 0.0
            
            # Частота переключений = количество переключений / время в минутах
            switches = sum(1 for i in range(len(apps) - 1) if apps[i] != apps[i + 1])
            time_minutes = 15 / 60  # 15 сек = 0.25 мин
            
            return switches / time_minutes if time_minutes > 0 else 0.0
        except Exception as e:
            logger.debug(f"Error calculating switch frequency: {e}")
            return 0.0
    
    def _calculate_afk_percentage(self, afk_events: List[Dict[str, Any]]) -> float:
        """Расчет процента AFK времени за последний период"""
        if not afk_events:
            return 0.0
        
        try:
            afk_duration = 0
            total_duration = 0
            
            for event in afk_events:
                if isinstance(event, dict) and "duration" in event:
                    total_duration += event["duration"]
                    if event.get("data", {}).get("status") == "afk":
                        afk_duration += event["duration"]
            
            if total_duration == 0:
                return 0.0
            
            return (afk_duration / total_duration) * 100
        except Exception as e:
            logger.debug(f"Error calculating AFK percentage: {e}")
            return 0.0
    
    def _is_afk(self, afk_events: List[Dict[str, Any]]) -> bool:
        """Проверка, находится ли пользователь в AFK статусе"""
        if not afk_events:
            return False
        
        try:
            latest = afk_events[-1] if isinstance(afk_events, list) else afk_events
            if isinstance(latest, dict):
                return latest.get("data", {}).get("status") == "afk"
        except Exception:
            pass
        
        return False
    
    def extract_text_features(self, text: str) -> Dict[str, float]:
        """
        Извлечение текстовых признаков из имени приложения, заголовка или URL
        
        Args:
            text: текст для анализа
            
        Returns:
            Словарь с бинарными признаками
        """
        features = {}
        text_lower = text.lower()
        
        # Ищем ключевые слова для категорий
        for category, keywords_dict in CATEGORY_KEYWORDS.items():
            all_keywords = keywords_dict.get("apps", []) + keywords_dict.get("urls", [])
            for keyword in all_keywords:
                feature_name = f"{category}_{keyword}"
                features[feature_name] = 1.0 if keyword in text_lower else 0.0
        
        return features
    
    def categorize_activity(
        self,
        app_name: str,
        window_title: str,
        url: str,
        classifier_func=None
    ) -> Tuple[str, float]:
        """
        Категоризация активности (rule-based или ML)
        
        Args:
            app_name: имя приложения
            window_title: заголовок окна
            url: URL
            classifier_func: функция ML-классификатора (если доступна)
            
        Returns:
            Кортеж (категория, confidence)
        """
        text = f"{app_name} {window_title} {url}".lower()
        
        # Сначала пытаемся ML классификатор
        if classifier_func is not None:
            try:
                return classifier_func(text)
            except Exception as e:
                logger.debug(f"ML classifier failed: {e}")
        
        # Rule-based классификация
        scores = {
            "work": 0.0,
            "communication": 0.0,
            "distraction": 0.0,
            "break": 0.0,
            "neutral": 0.5,  # по умолчанию
            "unknown": 0.0
        }
        
        for category, keywords_dict in CATEGORY_KEYWORDS.items():
            all_keywords = keywords_dict.get("apps", []) + keywords_dict.get("urls", [])
            matches = sum(1 for kw in all_keywords if kw in text)
            if matches > 0:
                scores[category] = min(0.9, 0.5 + matches * 0.1)
        
        # Выбираем категорию с максимальным баллом
        best_category = max(scores, key=scores.get)
        confidence = scores[best_category]
        
        if confidence < 0.3:
            return "unknown", 0.0
        
        return best_category, confidence
    
    def is_distraction(self, app_name: str, url: str, confidence_threshold: float = 0.5) -> bool:
        """Проверка, является ли активность отвлечением"""
        text = f"{app_name} {url}".lower()
        
        # Ищем ключевые слова отвлечения
        distraction_matches = sum(
            1 for keyword in DISTRACTION_KEYWORDS if keyword in text
        )
        
        return distraction_matches > 0
