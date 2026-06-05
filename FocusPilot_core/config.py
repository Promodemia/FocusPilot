"""
FocusPilot Configuration
Глобальные конфигурационные параметры
"""

import os
from pathlib import Path

# ============================================================================
# Пути
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.absolute()
MODELS_DIR = PROJECT_ROOT / "models"
DB_PATH = PROJECT_ROOT / "focuspilot.db"
LOG_FILE = PROJECT_ROOT / "focuspilot.log"

# Создаем директории если их нет
MODELS_DIR.mkdir(exist_ok=True)

# ============================================================================
# ActivityWatch
# ============================================================================

AW_HOST = "localhost"
AW_PORT = 5600
AW_TIMEOUT = 5  # секунды

# ============================================================================
# Мониторинг активности
# ============================================================================

# Интервал опроса новых событий (секунды)
POLL_INTERVAL = 2.0

# Минимальная длительность отвлечения для уведомления (минуты)
DISTRACTION_NOTIFICATION_THRESHOLD = 2

# Вероятность отвлечения для уведомления
DISTRACTION_PROBABILITY_THRESHOLD = 0.7

# Размер окна для анализа временных рядов
PREDICTOR_WINDOW_SIZE = 30

# ============================================================================
# ML Модели
# ============================================================================

# Пути к моделям
CLASSIFIER_MODEL_PATH = MODELS_DIR / "classifier.joblib"
CLASSIFIER_VECTORIZER_PATH = MODELS_DIR / "classifier_vectorizer.joblib"
CLASSIFIER_SCALER_PATH = MODELS_DIR / "classifier_scaler.joblib"

PREDICTOR_MODEL_PATH = MODELS_DIR / "predictor.joblib"

# Параметры обучения RandomForest классификатора
CLASSIFIER_CONFIG = {
    "n_estimators": 100,
    "max_depth": 10,
    "min_samples_split": 5,
    "min_samples_leaf": 2,
    "random_state": 42,
}

# Параметры обучения TimeSeriesForest предсказателя
PREDICTOR_CONFIG = {
    "n_estimators": 50,
    "max_depth": 8,
    "min_samples_split": 5,
    "random_state": 42,
}

# ============================================================================
# Обучение моделей
# ============================================================================

# Ежедневное обучение
NIGHTLY_TRAINING_ENABLED = True
NIGHTLY_TRAINING_HOUR = 2  # 2:00 AM
NIGHTLY_TRAINING_MINUTE = 0

# История данных для обучения (дней)
TRAINING_DATA_HISTORY_DAYS = 14

# Минимальное количество примеров для обучения
MIN_TRAINING_SAMPLES = 10

# ============================================================================
# База данных
# ============================================================================

# Периодичность сохранения статистики (минут)
STATS_SAVE_INTERVAL = 30

# Максимальное количество обучающих примеров в памяти
MAX_TRAINING_SAMPLES_IN_MEMORY = 10000

# ============================================================================
# Уведомления
# ============================================================================

# Интервал между уведомлениями (секунды)
NOTIFICATION_COOLDOWN = 120

# Таймаут уведомления (секунды)
NOTIFICATION_TIMEOUT = 10

# ============================================================================
# GUI
# ============================================================================

# Размеры главного окна
MAIN_WINDOW_WIDTH = 900
MAIN_WINDOW_HEIGHT = 700

# Интервал обновления UI (миллисекунды)
UI_UPDATE_INTERVAL = 1000

# ============================================================================
# Категории активности
# ============================================================================

ACTIVITY_CATEGORIES = [
    "work",
    "communication",
    "distraction",
    "neutral",
    "break",
    "unknown",
]

# Mapping категорий по цветам
CATEGORY_COLORS = {
    "work": "#4CAF50",  # Green
    "communication": "#2196F3",  # Blue
    "distraction": "#FF5722",  # Red Orange
    "neutral": "#9E9E9E",  # Gray
    "break": "#FFC107",  # Amber
    "unknown": "#757575",  # Dark Gray
}

# ============================================================================
# Ключевые слова для категоризации
# ============================================================================

WORK_KEYWORDS = [
    "code", "vscode", "pycharm", "idea", "visual studio", "sublime",
    "notepad++", "atom", "cursor", "rider", "github", "stackoverflow",
    "docs", "devdocs", "jira", "confluence", "gitlab", "bitbucket",
    "google.com/search", "programming", "development", "coding"
]

COMMUNICATION_KEYWORDS = [
    "slack", "teams", "discord", "telegram", "mail", "outlook",
    "thunderbird", "skype", "zoom", "whatsapp", "telegram.org",
    "gmail", "meetings", "chat", "message", "email"
]

DISTRACTION_KEYWORDS = [
    "youtube", "tiktok", "instagram", "facebook", "twitter", "reddit",
    "twitch", "netflix", "spotify", "steam", "gaming", "games",
    "social", "entertainment"
]

BREAK_KEYWORDS = [
    "media player", "vlc", "foobar", "music", "video",
    "coffee", "lunch", "break", "rest", "snack", "break"
]

# ============================================================================
# Логирование
# ============================================================================

LOG_LEVEL = "INFO"

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Ротация логов
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5

# ============================================================================
# Отладка
# ============================================================================

DEBUG_MODE = False

# Сохранение подробных логов
VERBOSE_LOGGING = False

# ============================================================================
# Функции помощи
# ============================================================================

def get_classifier_model_path():
    """Получить путь к модели классификатора"""
    return str(CLASSIFIER_MODEL_PATH)

def get_predictor_model_path():
    """Получить путь к модели предсказателя"""
    return str(PREDICTOR_MODEL_PATH)

def get_db_path():
    """Получить путь к базе данных"""
    return str(DB_PATH)

def get_log_file():
    """Получить путь к файлу логов"""
    return str(LOG_FILE)

def print_config():
    """Вывести конфигурацию"""
    print("\n" + "="*60)
    print("FocusPilot Configuration")
    print("="*60)
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Models Directory: {MODELS_DIR}")
    print(f"Database Path: {DB_PATH}")
    print(f"Log File: {LOG_FILE}")
    print(f"\nActivityWatch: {AW_HOST}:{AW_PORT}")
    print(f"Poll Interval: {POLL_INTERVAL}s")
    print(f"Distraction Threshold: {DISTRACTION_NOTIFICATION_THRESHOLD}min")
    print(f"Nightly Training: {NIGHTLY_TRAINING_ENABLED} at {NIGHTLY_TRAINING_HOUR:02d}:{NIGHTLY_TRAINING_MINUTE:02d}")
    print("="*60 + "\n")

if __name__ == "__main__":
    print_config()
