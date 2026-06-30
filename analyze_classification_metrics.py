#!/usr/bin/env python3
"""
Скрипт для анализа метрик классификации
Вычисляет Precision, Recall, F1-score и строит confusion matrix
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import sys

try:
    import numpy as np
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import (
        classification_report, confusion_matrix, roc_auc_score, roc_curve,
        accuracy_score, precision_score, recall_score, f1_score
    )
    from sklearn.feature_extraction.text import TfidfVectorizer
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("Требуется scikit-learn. Установите: pip install scikit-learn")
    sys.exit(1)

# Определяем возможные пути к БД
DB_PATHS = [
    Path("gui/backend/focuspilot.db"),
    Path("FocusPilot_core/focuspilot.db"),
    Path("focuspilot.db"),
]

CATEGORIES = ["work", "communication", "distraction", "neutral", "break"]

def find_db():
    """Найти файл БД"""
    for db_path in DB_PATHS:
        if db_path.exists():
            return db_path
    return None

def load_training_data(db_path):
    """Загрузить данные обучения из БД"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT app_name, category, features
        FROM training_data
        ORDER BY timestamp DESC
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    X_text = []
    X_numerical = []
    y = []
    
    for app_name, category, features_json in rows:
        # Пропускаем неизвестные категории
        if category not in CATEGORIES:
            continue
        
        # Текстовые признаки
        text = f"{app_name or ''}"
        X_text.append(text)
        
        # Численные признаки
        features = json.loads(features_json) if features_json else {}
        numerical = [
            features.get("hour_of_day", 0) / 24.0,
            features.get("day_of_week", 0) / 7.0,
            features.get("focus_duration", 0) / 3600.0,
            features.get("switch_frequency", 0) / 100.0,
            features.get("afk_percentage", 0) / 100.0,
            1.0 if features.get("is_afk") else 0.0,
        ]
        X_numerical.append(numerical)
        y.append(category)
    
    return X_text, X_numerical, y

def analyze_metrics():
    """Анализировать метрики классификации"""
    db_path = find_db()
    
    if not db_path:
        print("Ошибка: файл БД не найден.")
        return
    
    print(f"Загружаю данные из: {db_path}")
    print("=" * 80)
    
    X_text, X_numerical, y = load_training_data(db_path)
    
    if len(X_text) < 20:
        print(f"Ошибка: недостаточно данных ({len(X_text)} примеров). Требуется минимум 20.")
        return
    
    print(f"Загружено {len(X_text)} примеров\n")
    
    # Векторизация текста
    print("Предварительная обработка...")
    vectorizer = TfidfVectorizer(max_features=100, ngram_range=(1, 2))
    X_text_vec = vectorizer.fit_transform(X_text).toarray()
    
    # Масштабирование численных признаков
    scaler = StandardScaler()
    X_numerical = np.array(X_numerical)
    X_numerical_scaled = scaler.fit_transform(X_numerical)
    
    # Комбинирование признаков
    X = np.hstack([X_text_vec, X_numerical_scaled])
    
    # Train/Test Split
    test_size = 0.2
    min_test_size = max(1, int(len(X) * test_size))
    
    if len(X) < 10:
        print("Ошибка: слишком мало данных для разделения на train/test")
        return
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )
    
    print(f"Train: {len(X_train)} примеров, Test: {len(X_test)} примеров\n")
    
    # Обучение классификатора
    print("Обучение RandomForest классификатора...")
    clf = RandomForestClassifier(
        n_estimators=100, max_depth=10, min_samples_split=5,
        min_samples_leaf=2, random_state=42, n_jobs=-1
    )
    clf.fit(X_train, y_train)
    
    # Предсказание
    y_pred = clf.predict(X_test)
    y_pred_proba = clf.predict_proba(X_test)
    
    # Общие метрики
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\nОБЩАЯ ТОЧНОСТЬ (Accuracy): {accuracy:.4f} ({accuracy*100:.1f}%)\n")
    
    # Детальный отчет
    print("ДЕТАЛЬНЫЕ МЕТРИКИ ПО КЛАССАМ:")
    print("=" * 80)
    print(classification_report(y_test, y_pred, digits=4, target_names=CATEGORIES))
    
    # Confusion Matrix
    print("\nMATRIX ОШИБОК (Confusion Matrix):")
    print("-" * 80)
    
    cm = confusion_matrix(y_test, y_pred, labels=CATEGORIES)
    
    # Форматированный вывод
    max_len = max(len(cat) for cat in CATEGORIES)
    header = " " * (max_len + 2) + "  ".join(f"{cat:>8}" for cat in CATEGORIES)
    print(header)
    print("-" * len(header))
    
    for i, cat in enumerate(CATEGORIES):
        row_str = f"{cat:<{max_len}} | " + "  ".join(f"{cm[i,j]:>8}" for j in range(len(CATEGORIES)))
        print(row_str)
    
    print("\nПримечание: столбцы - предсказанные классы, строки - истинные классы\n")
    
    # ROC-AUC для binary classification (distraction vs. rest)
    print("АНАЛИЗ КАТЕГОРИИ 'DISTRACTION':")
    print("-" * 80)
    
    y_test_binary = [1 if cat == "distraction" else 0 for cat in y_test]
    y_pred_proba_distraction = y_pred_proba[:, CATEGORIES.index("distraction")]
    
    try:
        roc_auc = roc_auc_score(y_test_binary, y_pred_proba_distraction)
        print(f"ROC-AUC (distraction vs. rest): {roc_auc:.4f}")
        
        # Optimal threshold
        fpr, tpr, thresholds = roc_curve(y_test_binary, y_pred_proba_distraction)
        optimal_idx = np.argmax(tpr - fpr)
        optimal_threshold = thresholds[optimal_idx]
        print(f"Оптимальный порог вероятности: {optimal_threshold:.3f}\n")
    except Exception as e:
        print(f"Не удалось вычислить ROC-AUC: {e}\n")
    
    # Статистика обучающей выборки
    print("СТАТИСТИКА ВЫБОРКИ:")
    print("-" * 80)
    
    category_counts = Counter(y)
    total = len(y)
    
    for cat in CATEGORIES:
        count = category_counts[cat]
        percentage = (count / total) * 100
        print(f"  {cat:<15}: {count:>4} примеров ({percentage:>5.1f}%)")
    
    print(f"  {'ИТОГО':<15}: {total:>4} примеров")
    
    # Рекомендации
    print("\n\nРЕКОМЕНДАЦИИ:")
    print("-" * 80)
    
    if accuracy < 0.70:
        print("  ⚠ Низкая точность классификации (< 70%)")
        print("    Требуется больше размеченных данных или улучшение признаков")
    elif accuracy < 0.80:
        print("  ⚠ Средняя точность классификации (70-80%)")
        print("    Рекомендуется добавить больше примеров для слабо представленных классов")
    else:
        print("  ✓ Хорошая точность классификации (> 80%)")
    
    if min(category_counts.values()) < 10:
        print("  ⚠ Мало примеров для некоторых классов")
        print(f"    Минимум: {min(category_counts.values())} примеров")
        print("    Рекомендуется минимум 20-30 примеров на класс")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    analyze_metrics()
