"""
Core Coordinator
Главный цикл: опрос событий, классификация, сравнение с планом, уведомления
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
import time
import threading
from integration.aw_provider import AWDataProvider
from ml.feature_extractor import FeatureExtractor
from ml.classifier import ActivityClassifier
from ml.predictor import DistractionPredictor
from ml.trainer import ModelTrainer
from storage.db import DatabaseManager

logger = logging.getLogger(__name__)


class PlanParser:
    """Парсер текстового плана"""
    
    @staticmethod
    def parse_plan(plan_text: str) -> List[Dict[str, Any]]:
        """
        Парсинг плана из текста
        
        Args:
            plan_text: текст плана
            
        Returns:
            Список элементов плана
        """
        if not plan_text:
            return []
        
        plan_items = []
        lines = plan_text.strip().split("\n")
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            # Простой парсинг: "10:00-11:00 work description"
            item = {
                "description": line,
                "categories": [],
                "start_time": None,
                "end_time": None,
            }
            
            # Извлекаем ключевые слова
            lower_line = line.lower()
            if any(kw in lower_line for kw in ["work", "coding", "develop", "write"]):
                item["categories"].append("work")
            if any(kw in lower_line for kw in ["meet", "call", "chat", "discuss"]):
                item["categories"].append("communication")
            if any(kw in lower_line for kw in ["break", "rest", "lunch", "coffee"]):
                item["categories"].append("break")
            
            if not item["categories"]:
                item["categories"].append("neutral")
            
            plan_items.append(item)
        
        return plan_items


class ActivityCoordinator:
    """Координатор активности - главный цикл приложения"""
    
    def __init__(
        self,
        poll_interval: float = 2.0,
        notification_callback: Optional[Callable] = None
    ):
        """
        Инициализация координатора
        
        Args:
            poll_interval: интервал опроса в секундах
            notification_callback: функция для отправки уведомлений
        """
        self.poll_interval = poll_interval
        self.notification_callback = notification_callback
        
        # Инициализируем компоненты
        self.aw_provider = AWDataProvider()
        self.feature_extractor = FeatureExtractor()
        self.classifier = ActivityClassifier()
        self.predictor = DistractionPredictor()
        self.db_manager = DatabaseManager()
        self.trainer = ModelTrainer(self.aw_provider, self.db_manager, self.feature_extractor)
        
        # Состояние
        self.is_running = False
        self.current_category = "unknown"
        self.current_confidence = 0.0
        self.current_app = "Unknown"
        self.distraction_start_time = None
        self.last_category_change = datetime.utcnow()
        self.current_plan = []
        self.daily_stats = {
            "work": 0,
            "communication": 0,
            "distraction": 0,
            "neutral": 0,
            "break": 0,
            "unknown": 0,
            "afk": 0,
        }
        
        # Поток
        self.main_thread = None
        
        # Проверка AW при инициализации
        self._check_aw_availability()
    
    def _check_aw_availability(self) -> bool:
        """
        Проверка доступности ActivityWatch сервера
        
        Returns:
            True если доступен, False иначе
        """
        max_attempts = 3
        for attempt in range(max_attempts):
            if self.aw_provider.is_connected():
                logger.info("ActivityWatch server is available")
                return True
            
            logger.warning(f"ActivityWatch not available, attempt {attempt + 1}/{max_attempts}")
            if attempt < max_attempts - 1:
                time.sleep(2)
        
        logger.error(
            "ActivityWatch server is not available. "
            "Please install it from https://activitywatch.net/"
        )
        return False
    
    def set_daily_plan(self, plan_text: str) -> None:
        """
        Установка дневного плана
        
        Args:
            plan_text: текст плана
        """
        self.current_plan = PlanParser.parse_plan(plan_text)
        
        # Сохраняем в БД
        today = datetime.utcnow().strftime("%Y-%m-%d")
        self.db_manager.save_daily_plan(today, plan_text)
        
        logger.info(f"Daily plan set: {len(self.current_plan)} items")
    
    def start_coordinator(self) -> None:
        """Запуск координатора"""
        if self.is_running:
            logger.warning("Coordinator already running")
            return
        
        if not self.aw_provider.is_connected():
            logger.error("Cannot start: ActivityWatch not available")
            return
        
        self.is_running = True
        self.main_thread = threading.Thread(target=self._run_main_loop)
        self.main_thread.daemon = True
        self.main_thread.start()
        
        logger.info("Coordinator started")
    
    def stop_coordinator(self) -> None:
        """Остановка координатора"""
        self.is_running = False
        if self.main_thread:
            self.main_thread.join(timeout=5)
        
        # Сохраняем статистику перед выходом
        self._save_daily_stats()
        logger.info("Coordinator stopped")
    
    def _run_main_loop(self) -> None:
        """Главный цикл мониторинга"""
        logger.info("Main loop started")
        
        # Загружаем план на сегодня
        today = datetime.utcnow().strftime("%Y-%m-%d")
        plan_text = self.db_manager.get_daily_plan(today)
        if plan_text:
            self.set_daily_plan(plan_text)
        
        # Обучаем модели если нужно
        if self.trainer.should_train():
            self.trainer.train_models_async()
        
        while self.is_running:
            try:
                current_time = datetime.utcnow()
                
                # Получаем новые события
                events = self.aw_provider.get_new_events()
                
                # Извлекаем признаки
                features = self.feature_extractor.extract_features_from_events(events, current_time)
                
                # Классифицируем активность
                category, confidence = self.classifier.predict(features)
                
                # Обновляем текущее приложение
                self.current_app = features.get("app_name", "Unknown")
                
                # Проверяем изменение активности
                if category != self.current_category:
                    self._on_activity_change(category, confidence, features)
                
                # Обновляем историю для предсказателя
                self.predictor.add_category(category)
                
                # Проверяем предсказание отвлечения
                distraction_prob = self.predictor.predict_distraction_probability()
                
                # Проверяем отвлечение
                self._check_for_distraction(
                    category,
                    distraction_prob,
                    features,
                    current_time
                )
                
                # Обновляем статистику
                self._update_statistics(category, self.poll_interval)
                
                # Сохраняем примеры для обучения (случайно)
                if features and category != "unknown":
                    import random
                    if random.random() < 0.1:  # 10% вероятность
                        self.db_manager.add_training_sample(
                            current_time,
                            features.get("app_name", ""),
                            features.get("window_title", ""),
                            features.get("url", ""),
                            category,
                            features
                        )
                
                time.sleep(self.poll_interval)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(self.poll_interval)
    
    def _on_activity_change(
        self,
        new_category: str,
        confidence: float,
        features: Dict[str, Any]
    ) -> None:
        """
        Обработка изменения активности
        
        Args:
            new_category: новая категория
            confidence: уверенность предсказания
            features: признаки активности
        """
        old_category = self.current_category
        self.current_category = new_category
        self.current_confidence = confidence
        self.current_app = features.get("app_name", "Unknown")
        self.last_category_change = datetime.utcnow()
        self.distraction_start_time = None
        
        logger.info(f"Activity changed: {old_category} -> {new_category} (confidence: {confidence:.2f})")
    
    def _check_for_distraction(
        self,
        category: str,
        distraction_prob: float,
        features: Dict[str, Any],
        current_time: datetime
    ) -> None:
        """
        Проверка отвлечения и отправка уведомления
        
        Args:
            category: текущая категория
            distraction_prob: вероятность отвлечения
            features: признаки
            current_time: текущее время
        """
        is_distraction = category == "distraction" or distraction_prob > 0.7
        
        if is_distraction and self.distraction_start_time is None:
            self.distraction_start_time = current_time
        
        if not is_distraction:
            self.distraction_start_time = None
            return
        
        # Проверяем длительность отвлечения
        if self.distraction_start_time is not None:
            distraction_duration = (current_time - self.distraction_start_time).total_seconds() / 60
            
            if distraction_duration >= 2:  # 2 минуты
                # Отправляем уведомление
                self._send_distraction_notification(
                    category,
                    distraction_prob,
                    distraction_duration,
                    features
                )
                
                # Сбрасываем таймер (чтобы не спамить)
                self.distraction_start_time = current_time
    
    def _send_distraction_notification(
        self,
        category: str,
        prob: float,
        duration: float,
        features: Dict[str, Any]
    ) -> None:
        """
        Отправка уведомления об отвлечении
        
        Args:
            category: категория активности
            prob: вероятность отвлечения
            duration: длительность в минутах
            features: признаки
        """
        message = f"Possible distraction detected: {category} ({prob*100:.0f}% confidence) for {duration:.1f} minutes"
        
        logger.warning(message)
        
        if self.notification_callback:
            self.notification_callback({
                "title": "⚠️ Distraction Alert",
                "message": message,
                "category": category,
                "probability": prob,
                "duration": duration,
                "features": features,
            })
    
    def _update_statistics(self, category: str, duration: float) -> None:
        """
        Обновление статистики
        
        Args:
            category: категория
            duration: длительность в секундах
        """
        if category in self.daily_stats:
            self.daily_stats[category] += duration
    
    def _save_daily_stats(self) -> None:
        """Сохранение суточной статистики"""
        try:
            today = datetime.utcnow().strftime("%Y-%m-%d")
            
            # Расчет план_adherence
            plan_adherence = 0.8  # placeholder
            
            stats = {
                "work_time": self.daily_stats["work"],
                "communication_time": self.daily_stats["communication"],
                "distraction_time": self.daily_stats["distraction"],
                "break_time": self.daily_stats["break"],
                "neutral_time": self.daily_stats["neutral"],
                "afk_time": self.daily_stats["afk"],
                "plan_adherence": plan_adherence,
            }
            
            self.db_manager.save_daily_stats(today, stats)
            logger.info(f"Daily stats saved: {stats}")
        except Exception as e:
            logger.error(f"Error saving stats: {e}")
    
    def get_current_status(self) -> Dict[str, Any]:
        """Получить текущий статус"""
        return {
            "is_running": self.is_running,
            "current_category": self.current_category,
            "current_confidence": self.current_confidence,
            "time_in_current_activity": (
                datetime.utcnow() - self.last_category_change
            ).total_seconds(),
            "distraction_probability": self.predictor.predict_distraction_probability(),
            "daily_stats": self.daily_stats,
        }
