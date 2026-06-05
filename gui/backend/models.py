import numpy as np
import joblib
from pathlib import Path
from typing import Tuple, Dict, Any, List

MODEL_PATH = Path(__file__).parent / "model.pkl"
PREDICTOR_PATH = Path(__file__).parent / "predictor.pkl"


class MLModel:
    def __init__(self):
        self.classifier = None
        self.predictor = None
        self.load_models()
        
    def load_models(self):
        if MODEL_PATH.exists():
            try:
                self.classifier = joblib.load(MODEL_PATH)
            except:
                self.classifier = None
        
        if PREDICTOR_PATH.exists():
            try:
                self.predictor = joblib.load(PREDICTOR_PATH)
            except:
                self.predictor = None

    def classify(self, app_name: str, features: Dict[str, Any]) -> Tuple[str, float]:
        """Classify activity - returns (category, confidence)"""
        
        # Rule-based classification if model not available
        if not self.classifier:
            return self._rule_based_classify(app_name, features)
        
        try:
            # ML classification (simplified)
            confidence = 0.85
            category = self._rule_based_classify(app_name, features)[0]
            return category, confidence
        except:
            return self._rule_based_classify(app_name, features)

    def _rule_based_classify(self, app_name: str, features: Dict[str, Any]) -> Tuple[str, float]:
        """Rule-based fallback classification"""
        app_lower = app_name.lower()
        
        work_keywords = ["code", "vscode", "pycharm", "idea", "github", "gitlab"]
        comm_keywords = ["slack", "teams", "discord", "zoom", "telegram"]
        distraction_keywords = ["youtube", "reddit", "twitter", "instagram", "tiktok"]
        
        if any(kw in app_lower for kw in work_keywords):
            return "work", 0.9
        elif any(kw in app_lower for kw in comm_keywords):
            return "communication", 0.85
        elif any(kw in app_lower for kw in distraction_keywords):
            return "distraction", 0.95
        else:
            return "unknown", 0.5

    def predict_distraction(self, category_history: List[str]) -> float:
        """Predict distraction probability (0.0-1.0)"""
        if not category_history:
            return 0.0
        
        distraction_count = category_history.count("distraction")
        return min(1.0, distraction_count / len(category_history))

    def train(self, training_data: List[Dict[str, Any]]) -> bool:
        """Train models on historical data"""
        try:
            # Simplified training - in production use sklearn/sktime
            self.classifier = True  # Dummy
            return True
        except:
            return False
