# FocusPilot - Daily Plan Controller

FocusPilot — это десктоп-приложение для контроля плана дня с использованием **ActivityWatch** локального сервера и машинного обучения.

## Возможности

✅ **Мониторинг активности в реальном времени** - получение данных только из ActivityWatch (локально)  
✅ **ML-классификация активности** - автоматическая категоризация на work, communication, distraction, break, neutral  
✅ **Прогнозирование отвлечений** - предсказание вероятности отвлечения на основе временных рядов  
✅ **Текстовый ввод плана** - простое парсирование расписания на естественном языке  
✅ **Уведомления об отвлечениях** - системные уведомления при превышении 2 минут отвлечения  
✅ **Статистика и отчеты** - просмотр фактического времени vs. плана, рекомендации  
✅ **Ежедневное обучение** - автоматическое переобучение моделей на исторических данных  

## Требования

- **Python 3.10+**
- **ActivityWatch** - локальный сервер для отслеживания активности
  - Скачать: https://activitywatch.net/
  - или через пакетный менеджер:
    - Windows: `choco install activitywatch`
    - macOS: `brew install activitywatch`
    - Linux: `sudo apt install activitywatch` (если доступен)

## Установка

### 1. Клонируйте/скачайте проект

```bash
cd FocusPilot
```

### 2. Создайте виртуальное окружение

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Установите зависимости

```bash
pip install -r requirements.txt
```

### 4. Запустите ActivityWatch

```bash
# Убедитесь, что aw-server запущен
# Windows: aw-server.exe (из установки ActivityWatch)
# Linux/macOS: aw-server
```

## Использование

### Запуск приложения

```bash
# Режим с трей иконкой (фоновый)
python main.py

# Режим с Qt окном
python main.py --qt
```

### Ввод дневного плана

В главном окне перейдите на вкладку "Daily Plan" и введите план:

```
9:00-10:00 Work on project
10:00-10:15 Break
10:15-12:00 Meeting with team
12:00-13:00 Lunch
13:00-15:00 Coding
15:00-15:15 Coffee break
15:15-17:00 Documentation
```

Приложение автоматически распознает ключевые слова:
- **Work**: coding, develop, write, project, design, develop
- **Communication**: meet, call, chat, discuss, presentation, review
- **Break**: break, rest, lunch, coffee, snack

### Обучение моделей

Модели обучаются автоматически каждый день в 2:00 AM на основе размеченных данных из ActivityWatch.

Для однократного обучения:

```bash
python train_nightly.py --once
```

Для ежедневного расписания:

```bash
python train_nightly.py
```

## Архитектура

### Модули

```
FocusPilot/
├── integration/
│   └── aw_provider.py          # Интеграция с ActivityWatch
├── ml/
│   ├── feature_extractor.py    # Извлечение признаков
│   ├── classifier.py           # RandomForest классификатор
│   ├── predictor.py            # TimeSeriesForest прогнозатор
│   └── trainer.py              # Обучение моделей
├── core/
│   └── coordinator.py          # Главный цикл мониторинга
├── gui/
│   ├── main_window.py          # PyQt5 главное окно
│   ├── tray_icon.py            # Трей иконка
│   └── notifications.py        # Система уведомлений
├── storage/
│   └── db.py                   # SQLite база данных
├── models/                      # Сохраненные ML модели
├── main.py                      # Точка входа
├── train_nightly.py             # Ночное обучение
└── requirements.txt             # Зависимости
```

### Компоненты

1. **AWDataProvider** - получение событий из ActivityWatch
   - `get_new_events()` - события за последние 15 сек
   - `get_historical_events(start, end)` - исторические события

2. **FeatureExtractor** - построение векторов признаков
   - app_name, window_title, url
   - hour_of_day, day_of_week
   - focus_duration, switch_frequency, afk_percentage

3. **ActivityClassifier** - RandomForest для категоризации
   - Обучается на размеченных данных
   - Использует TfidfVectorizer для текстов
   - Категории: work, communication, distraction, neutral, break, unknown

4. **DistractionPredictor** - прогноз отвлечений
   - Анализирует последовательность последних 30 категорий
   - Возвращает вероятность отвлечения на 5 минут вперед

5. **ActivityCoordinator** - главный цикл
   - Опрос событий каждые 2 секунды
   - Классификация активности
   - Сравнение с планом
   - Отправка уведомлений

6. **DatabaseManager** - SQLite база
   - daily_plan - дневные планы
   - training_data - размеченные примеры
   - feedback_log - действия пользователя
   - daily_stats - суточная статистика

## Использованные библиотеки

- **aw-client** - клиент ActivityWatch
- **scikit-learn** - ML модели (RandomForest, TfidfVectorizer)
- **sktime** - временные ряды
- **pandas/numpy** - работа с данными
- **PyQt5** - GUI
- **pystray** - трей иконка
- **plyer** - системные уведомления
- **joblib** - сохранение моделей
- **dateparser** - парсинг дат/времени

## Логирование

Все логи сохраняются в `focuspilot.log`:

```bash
# Просмотр логов
tail -f focuspilot.log
```

## Обработка ошибок

- Если ActivityWatch недоступен при старте - выводится инструкция по установке
- Если модели не обучены - используется rule-based классификатор (словарь ключевых слов)
- Если обучение ошибается - логируется и использует предыдущие модели
- Автоматическое переподключение к ActivityWatch при разрыве соединения

## Сценарии использования

### Сценарий 1: Мониторинг с уведомлениями

```
1. Запустить приложение: python main.py
2. Ввести дневной план через трей меню
3. Нажать "Start Monitoring"
4. При отвлечении на 2+ минуты - уведомление
5. Выбрать "Return to work" или "Ignore"
6. Статистика обновляется в реальном времени
```

### Сценарий 2: Анализ активности

```
1. Собрать 2+ недели данных в ActivityWatch
2. Запустить обучение: python train_nightly.py --once
3. После обучения классификатор будет более точным
4. Просмотреть статистику в главном окне
```

### Сценарий 3: Ночное автообучение

```
1. Запустить: python train_nightly.py
2. Скрипт обучает модели ежедневно в 2:00 AM
3. Модели сохраняются в models/ и автолоадятся при старте
```

## Рекомендации

- **Минимум 5-7 дней** для накопления данных перед первым обучением
- **Регулярно размечайте** активность в базе для лучшего обучения
- **Запускайте в фоне** с помощью трей иконки, чтобы не отвлекаться
- **Проверяйте логи** если есть проблемы с обучением

## FAQ

**Q: Почему нет облачных моделей?**  
A: FocusPilot работает полностью локально для конфиденциальности. Все данные остаются на вашем компьютере.

**Q: Какой размер модели?**  
A: RandomForest классификатор ~5MB, predictor ~2MB. Компактные и быстрые.

**Q: Можно ли использовать без ActivityWatch?**  
A: Нет, ActivityWatch - обязательная зависимость для получения данных о активности.

**Q: Какой процент CPU/RAM?**  
A: ~1-2% CPU в режиме мониторинга, 100-200MB RAM.

## Лицензия

MIT License

## Развитие

Планируемые функции:
- 📈 Расширенная визуализация графиков
- 📱 Синхронизация с TODO приложениями
- 🎨 Темы оформления
- 🔔 Кастомные правила уведомлений
- 📊 Экспорт отчетов в PDF

---

**Автор**: FocusPilot Team  
**Версия**: 1.0  
**Последнее обновление**: 2024
