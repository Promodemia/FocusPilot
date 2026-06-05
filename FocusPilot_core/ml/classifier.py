"""
Activity Classifier
RandomForest классификатор для категоризации активности
"""

import logging
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import os

logger = logging.getLogger(__name__)

# Категории активности
CATEGORIES = ["work", "communication", "distraction", "neutral", "break", "unknown"]

# Импорты scikit-learn
HAS_SKLEARN = True
try:
    from sklearn.ensemble import RandomForestClassifier as SklearnRFC
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.preprocessing import StandardScaler
    import joblib
except ImportError:
    SklearnRFC = None
    TfidfVectorizer = None
    StandardScaler = None
    joblib = None
    HAS_SKLEARN = False


class ActivityClassifier:
    """RandomForest классификатор для активности"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or "models/classifier.joblib"
        self.vectorizer_path = model_path.replace(".joblib", "_vectorizer.joblib") if model_path else "models/classifier_vectorizer.joblib"
        self.classifier = None
        self.vectorizer = TfidfVectorizer(max_features=100, ngram_range=(1, 2)) if HAS_SKLEARN else None
        self.scaler = StandardScaler() if HAS_SKLEARN else None
        self.is_trained = False
        if HAS_SKLEARN:
            self._load_model()

    def train(self, training_data: List[Dict[str, Any]], feature_extractor=None) -> bool:
        if not HAS_SKLEARN or not training_data or len(training_data) < 10:
            return False
        try:
            X_text = []
            X_numerical = []
            y = []
            for item in training_data:
                features = item.get("features", {})
                label = item.get("label", "unknown")
                text = f"{features.get('app_name', '')} {features.get('window_title', '')} {features.get('url', '')}"
                X_text.append(text)
                numerical = [
                    features.get("hour_of_day", 0) / 24,
                    features.get("day_of_week", 0) / 7,
                    features.get("focus_duration", 0) / 60,
                    features.get("switch_frequency", 0) / 10,
                    features.get("afk_percentage", 0) / 100,
                    1.0 if features.get("is_afk") else 0.0,
                ]
                X_numerical.append(numerical)
                if label not in CATEGORIES:
                    label = "unknown"
                y.append(label)
            X_text_vec = self.vectorizer.fit_transform(X_text).toarray()
            X_numerical = np.array(X_numerical)
            X_numerical_scaled = self.scaler.fit_transform(X_numerical)
            X = np.hstack([X_text_vec, X_numerical_scaled])
            self.classifier = SklearnRFC(
                n_estimators=100, max_depth=10, min_samples_split=5,
                min_samples_leaf=2, random_state=42, n_jobs=-1
            )
            self.classifier.fit(X, y)
            self.is_trained = True
            self._save_model()
            logger.info("Classifier trained successfully")
            return True
        except Exception as e:
            logger.error(f"Error training classifier: {e}")
            return False

    def predict(self, features: Dict[str, Any]) -> Tuple[str, float]:
        if not self.is_trained or self.classifier is None:
            return self._heuristic_predict(features)
        try:
            text = f"{features.get('app_name', '')} {features.get('window_title', '')} {features.get('url', '')}"
            X_text_vec = self.vectorizer.transform([text]).toarray()
            X_numerical = np.array([[
                features.get("hour_of_day", 0) / 24,
                features.get("day_of_week", 0) / 7,
                features.get("focus_duration", 0) / 60,
                features.get("switch_frequency", 0) / 10,
                features.get("afk_percentage", 0) / 100,
                1.0 if features.get("is_afk") else 0.0,
            ]])
            X_numerical_scaled = self.scaler.transform(X_numerical)
            X = np.hstack([X_text_vec, X_numerical_scaled])
            prediction = self.classifier.predict(X)[0]
            probabilities = self.classifier.predict_proba(X)[0]
            confidence = max(probabilities)
            return prediction, float(confidence)
        except Exception as e:
            logger.error(f"Error predicting: {e}")
            return self._heuristic_predict(features)

    def _heuristic_predict(self, features: Dict[str, Any]) -> Tuple[str, float]:
        app_name = features.get('app_name', '').lower()
        window_title = features.get('window_title', '').lower()
        if features.get("is_afk"):
            return "break", 0.9
        work_keywords = ["visual studio", "vscode", "pycharm", "notepad", "sublime", "code", "editor", "terminal"]
        if any(kw in app_name or kw in window_title for kw in work_keywords):
            return "work", 0.7
        distraction_keywords = ["youtube", "facebook", "instagram", "twitter", "reddit", "tiktok"]
        if any(kw in app_name or kw in window_title for kw in distraction_keywords):
            return "distraction", 0.7
        communication_keywords = ["slack", "telegram", "discord", "zoom", "skype", "teams"]
        if any(kw in app_name or kw in window_title for kw in communication_keywords):
            return "communication", 0.7
        return "neutral", 0.5

    def predict_proba(self, features: Dict[str, Any]) -> Dict[str, float]:
        if not self.is_trained or self.classifier is None:
            return {cat: 0.0 for cat in CATEGORIES}
        try:
            text = f"{features.get('app_name', '')} {features.get('window_title', '')} {features.get('url', '')}"
            X_text_vec = self.vectorizer.transform([text]).toarray()
            X_numerical = np.array([[
                features.get("hour_of_day", 0) / 24,
                features.get("day_of_week", 0) / 7,
                features.get("focus_duration", 0) / 60,
                features.get("switch_frequency", 0) / 10,
                features.get("afk_percentage", 0) / 100,
                1.0 if features.get("is_afk") else 0.0,
            ]])
            X_numerical_scaled = self.scaler.transform(X_numerical)
            X = np.hstack([X_text_vec, X_numerical_scaled])
            probabilities = self.classifier.predict_proba(X)[0]
            return {cat: float(prob) for cat, prob in zip(self.classifier.classes_, probabilities)}
        except Exception as e:
            logger.error(f"Error predicting probabilities: {e}")
            return {cat: 0.0 for cat in CATEGORIES}

    def _save_model(self) -> bool:
        if not HAS_SKLEARN:
            return False
        try:
            os.makedirs(os.path.dirname(self.model_path) or ".", exist_ok=True)
            joblib.dump(self.classifier, self.model_path)
            joblib.dump(self.vectorizer, self.vectorizer_path)
            joblib.dump(self.scaler, self.model_path.replace(".joblib", "_scaler.joblib"))
            logger.info(f"Model saved to {self.model_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            return False

    def _load_model(self) -> bool:
        if not HAS_SKLEARN:
            return False
        try:
            if os.path.exists(self.model_path):
                self.classifier = joblib.load(self.model_path)
                self.vectorizer = joblib.load(self.vectorizer_path)
                self.scaler = joblib.load(self.model_path.replace(".joblib", "_scaler.joblib"))
                self.is_trained = True
                logger.info(f"Model loaded from {self.model_path}")
                return True
        except Exception as e:
            logger.debug(f"Could not load model: {e}")
        return False

    def add_training_sample(self, features: Dict[str, Any], label: str) -> None:
        if label not in CATEGORIES:
            logger.warning(f"Invalid category: {label}")
            return
        logger.debug(f"Training sample added: {label}")

    def reset_model(self) -> None:
        self.classifier = None
        self.vectorizer = TfidfVectorizer(max_features=100, ngram_range=(1, 2)) if HAS_SKLEARN else None
        self.scaler = StandardScaler() if HAS_SKLEARN else None
        self.is_trained = False
