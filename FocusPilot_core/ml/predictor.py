"""
Distraction Predictor
TimeSeriesForest для прогноза вероятности отвлечения
"""

import logging
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DistractionPredictor:
    """Предсказатель вероятности отвлечения"""
    
    def __init__(self, model_path: Optional[str] = None, window_size: int = 30):
        """
        Инициализация предсказателя
        
        Args:
            model_path: путь для сохранения/загрузки модели
            window_size: размер окна для анализа временного ряда
        """
        self.model_path = model_path or "models/predictor.joblib"
        self.window_size = window_size
        self.model = None
        self.is_trained = False
        self.category_history = []
        
        self._load_model()

    def add_category(self, category: str) -> None:
        """
        Добавление категории в историю
        
        Args:
            category: категория активности
        """
        self.category_history.append(category)
        
        if len(self.category_history) > self.window_size * 2:
            self.category_history = self.category_history[-self.window_size * 2:]

    def predict_distraction_probability(self) -> float:
        """
        Предсказание вероятности отвлечения в ближайшие 5 минут
        
        Returns:
            Вероятность отвлечения (0.0 - 1.0)
        """
        if len(self.category_history) < self.window_size:
            return self._simple_prediction()

        try:
            if self.is_trained and self.model is not None:
                return self._ml_prediction()
            else:
                return self._simple_prediction()
        except Exception as e:
            logger.debug(f"Error in distraction prediction: {e}")
            return self._simple_prediction()

    def _ml_prediction(self) -> float:
        """ML-основанное предсказание"""
        try:
            window = self.category_history[-self.window_size:]
            category_codes = self._encode_categories(window)
            features = self._extract_time_series_features(category_codes)

            if len(features) > 0:
                prob = self.model.predict_proba(features.reshape(1, -1))[0][1]
                return float(prob)
        except Exception as e:
            logger.debug(f"ML prediction failed: {e}")

        return self._simple_prediction()

    def _simple_prediction(self) -> float:
        """Простая эвристическая предсказание"""
        if not self.category_history:
            return 0.0

        window = self.category_history[-self.window_size:]
        distraction_count = sum(1 for cat in window if cat == "distraction")
        base_prob = distraction_count / len(window)

        recent = window[-5:] if len(window) >= 5 else window
        recent_distractions = sum(1 for cat in recent if cat == "distraction")
        trend_factor = recent_distractions / len(recent) if recent else 0

        prediction = base_prob * 0.6 + trend_factor * 0.4
        return min(1.0, max(0.0, prediction))

    def _encode_categories(self, categories: List[str]) -> np.ndarray:
        """Кодирование категорий в числа"""
        encoding = {
            "work": 0,
            "communication": 1,
            "distraction": 2,
            "neutral": 3,
            "break": 4,
            "unknown": 5,
        }
        return np.array([encoding.get(cat, 5) for cat in categories])

    def _extract_time_series_features(self, codes: np.ndarray) -> np.ndarray:
        """Извлечение признаков из временного ряда"""
        features = []
        features.append(np.mean(codes))
        features.append(np.std(codes))
        features.append(np.max(codes) - np.min(codes))

        for i in range(6):
            features.append(np.sum(codes == i) / len(codes))

        x = np.arange(len(codes))
        slope = np.polyfit(x, codes, 1)[0]
        features.append(slope)

        if len(codes) > 1:
            autocorr = np.corrcoef(codes[:-1], codes[1:])[0, 1]
            features.append(np.nan_to_num(autocorr, 0.0))
        else:
            features.append(0.0)

        return np.array(features)

    def train(
        self,
        training_sequences: List[Dict[str, Any]],
        predictions: List[int]
    ) -> bool:
        """
        Обучение модели на исторических последовательностях
        
        Args:
            training_sequences: список последовательностей категорий
            predictions: список меток (0 - нет отвлечения, 1 - есть)

        Returns:
            True если обучение успешно
        """
        if not training_sequences or len(training_sequences) < 10:
            logger.warning("Insufficient training data for predictor")
            return False

        try:
            X = []
            y = predictions

            for seq in training_sequences:
                categories = seq.get("categories", [])
                if len(categories) >= self.window_size:
                    codes = self._encode_categories(categories[-self.window_size:])
                    features = self._extract_time_series_features(codes)
                    X.append(features)

            if len(X) < 10:
                logger.warning("Could not extract enough features")
                return False

            X = np.array(X)
            y = np.array(y[:len(X)])

            self.model = RandomForestClassifier(
                n_estimators=50,
                max_depth=8,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1
            )

            self.model.fit(X, y)
            self.is_trained = True
            self._save_model()
            logger.info("Predictor trained successfully")
            return True
        except Exception as e:
            logger.error(f"Error training predictor: {e}")
            return False

    def _save_model(self) -> bool:
        """Сохранение модели"""
        try:
            os.makedirs(os.path.dirname(self.model_path) or ".", exist_ok=True)
            joblib.dump(self.model, self.model_path)
            logger.info(f"Predictor model saved to {self.model_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving predictor model: {e}")
            return False

    def _load_model(self) -> bool:
        """Загрузка модели"""
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                self.is_trained = True
                logger.info(f"Predictor model loaded from {self.model_path}")
                return True
        except Exception as e:
            logger.debug(f"Could not load predictor model: {e}")

        return False

    def reset_history(self) -> None:
        """Сброс истории категорий"""
        self.category_history = []

    def get_history_stats(self) -> Dict[str, Any]:
        """Получить статистику истории"""
        if not self.category_history:
            return {
                "total_samples": 0,
                "distraction_ratio": 0.0,
                "category_distribution": {}
            }

        dist_count = self.category_history.count("distraction")
        category_dist = {
            "work": self.category_history.count("work"),
            "communication": self.category_history.count("communication"),
            "distraction": self.category_history.count("distraction"),
            "neutral": self.category_history.count("neutral"),
            "break": self.category_history.count("break"),
            "unknown": self.category_history.count("unknown"),
        }

        return {
            "total_samples": len(self.category_history),
            "distraction_ratio": dist_count / len(self.category_history),
            "category_distribution": category_dist
        }
