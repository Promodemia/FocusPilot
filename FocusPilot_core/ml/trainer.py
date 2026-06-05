"""
Model Trainer
Фоновый процесс для обучения моделей на исторических данных
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import threading
import time
from integration.aw_provider import AWDataProvider
from ml.feature_extractor import FeatureExtractor
from ml.classifier import ActivityClassifier
from ml.predictor import DistractionPredictor
from storage.db import DatabaseManager

logger = logging.getLogger(__name__)


class ModelTrainer:
    """Тренер для обучения ML моделей"""
    
    def __init__(
        self,
        aw_provider: Optional[AWDataProvider] = None,
        db_manager: Optional[DatabaseManager] = None,
        feature_extractor: Optional[FeatureExtractor] = None
    ):
        """
        Инициализация тренера
        
        Args:
            aw_provider: провайдер данных ActivityWatch
            db_manager: менеджер базы данных
            feature_extractor: экстрактор признаков
        """
        self.aw_provider = aw_provider or AWDataProvider()
        self.db_manager = db_manager or DatabaseManager()
        self.feature_extractor = feature_extractor or FeatureExtractor()
        
        self.classifier = ActivityClassifier()
        self.predictor = DistractionPredictor()
        
        self.is_training = False
        self.last_training_time = None
        self.training_thread = None
    
    def train_models_async(self) -> bool:
        """
        Асинхронный запуск обучения моделей
        
        Returns:
            True если обучение стартовано
        """
        if self.is_training:
            logger.warning("Training already in progress")
            return False
        
        self.training_thread = threading.Thread(target=self._train_models_internal)
        self.training_thread.daemon = True
        self.training_thread.start()
        return True
    
    def _train_models_internal(self) -> None:
        """Внутренний метод обучения (запускается в отдельном потоке)"""
        self.is_training = True
        logger.info("Starting model training")
        
        try:
            # Получение исторических данных
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=14)  # последние 14 дней
            
            logger.info(f"Fetching events from {start_time} to {end_time}")
            events = self.aw_provider.get_historical_events(start_time, end_time)
            
            if not events or all(len(v) == 0 for v in events.values()):
                logger.warning("No historical events found")
                self.is_training = False
                return
            
            # Извлечение признаков и построение обучающего набора
            training_data = self._build_training_data(events, start_time, end_time)
            
            if len(training_data) < 10:
                logger.warning("Insufficient training data")
                self.is_training = False
                return
            
            # Получение размеченных данных из БД
            labeled_data = self.db_manager.get_training_samples()
            
            # Обучение классификатора
            if labeled_data:
                logger.info(f"Training classifier with {len(labeled_data)} labeled samples")
                classifier_success = self.classifier.train(labeled_data, self.feature_extractor)
            else:
                logger.info("No labeled training data, classifier remains untrained")
                classifier_success = False
            
            # Обучение предсказателя отвлечений
            distraction_data = self._build_distraction_training_data(labeled_data)
            if len(distraction_data) > 0:
                logger.info(f"Training predictor with {len(distraction_data)} sequences")
                sequences = [d["sequence"] for d in distraction_data]
                labels = [1 if d["label"] == "distraction" else 0 for d in distraction_data]
                predictor_success = self.predictor.train(sequences, labels)
            else:
                logger.info("Insufficient data for predictor training")
                predictor_success = False
            
            # Обновление метаданных
            self.db_manager.update_model_metadata({
                "last_training": datetime.utcnow().isoformat(),
                "classifier_trained": classifier_success,
                "predictor_trained": predictor_success,
                "training_samples": len(labeled_data),
            })
            
            self.last_training_time = datetime.utcnow()
            logger.info("Model training completed successfully")
            
        except Exception as e:
            logger.error(f"Error during training: {e}")
        finally:
            self.is_training = False
    
    def _build_training_data(
        self,
        events: Dict[str, List[Dict[str, Any]]],
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Построение обучающего набора из событий
        
        Args:
            events: события от ActivityWatch
            start_time: начальное время
            end_time: конечное время
            
        Returns:
            Список примеров для обучения
        """
        training_data = []
        
        try:
            # Генерируем примеры каждые 5 минут
            current_time = start_time
            step = timedelta(minutes=5)
            
            while current_time < end_time:
                # Получаем события за текущее 5-минутное окно
                window_start = current_time
                window_end = current_time + step
                
                window_events = {
                    "window_events": [],
                    "url_events": [],
                    "afk_events": []
                }
                
                # Фильтруем события по временному окну
                for event_type, event_list in events.items():
                    for event in event_list:
                        try:
                            if isinstance(event, dict) and "timestamp" in event:
                                event_time = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
                                if window_start <= event_time < window_end:
                                    window_events[event_type].append(event)
                        except Exception:
                            pass
                
                # Извлекаем признаки
                if any(window_events.values()):
                    features = self.feature_extractor.extract_features_from_events(
                        window_events,
                        current_time
                    )
                    
                    training_data.append({
                        "features": features,
                        "label": "unknown"  # будет обновлено из размеченных данных
                    })
                
                current_time += step
            
            return training_data
            
        except Exception as e:
            logger.error(f"Error building training data: {e}")
            return []
    
    def _build_distraction_training_data(
        self,
        labeled_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Построение обучающих последовательностей для предсказателя
        
        Args:
            labeled_data: размеченные данные
            
        Returns:
            Список последовательностей
        """
        if len(labeled_data) < 30:
            return []
        
        sequences = []
        window_size = 30
        
        try:
            # Сортируем по времени
            sorted_data = sorted(
                labeled_data,
                key=lambda x: x.get("features", {}).get("timestamp", "")
            )
            
            # Создаем скользящие окна
            for i in range(len(sorted_data) - window_size):
                window = sorted_data[i:i + window_size]
                
                # Проверяем, что все в окне есть метки
                if all("label" in item for item in window):
                    categories = [item["label"] for item in window]
                    
                    # Определяем целевую метку (есть ли отвлечение в следующих 5 минутах)
                    next_window = sorted_data[i + window_size:min(i + window_size + 6, len(sorted_data))]
                    has_distraction = any(
                        item.get("label") == "distraction" for item in next_window
                    )
                    
                    sequences.append({
                        "sequence": {"categories": categories},
                        "label": "distraction" if has_distraction else "work"
                    })
            
            return sequences
            
        except Exception as e:
            logger.error(f"Error building distraction training data: {e}")
            return []
    
    def should_train(self) -> bool:
        """Проверка, нужно ли обучение (каждый день)"""
        if self.last_training_time is None:
            return True
        
        time_since_training = datetime.utcnow() - self.last_training_time
        return time_since_training > timedelta(days=1)
    
    def wait_for_training_complete(self, timeout: int = 300) -> bool:
        """
        Ожидание завершения обучения
        
        Args:
            timeout: таймаут в секундах
            
        Returns:
            True если обучение завершено
        """
        start_time = time.time()
        
        while self.is_training:
            if time.time() - start_time > timeout:
                logger.warning("Training timeout")
                return False
            time.sleep(1)
        
        return True
    
    def get_training_status(self) -> Dict[str, Any]:
        """Получить статус обучения"""
        return {
            "is_training": self.is_training,
            "last_training": self.last_training_time.isoformat() if self.last_training_time else None,
            "classifier_trained": self.classifier.is_trained,
            "predictor_trained": self.predictor.is_trained,
        }
