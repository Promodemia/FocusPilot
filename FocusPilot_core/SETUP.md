# FocusPilot - Подробное руководство по установке и запуску

## Предварительные требования

### Windows
- Python 3.10+ (скачать с https://www.python.org/)
- Git (опционально, для клонирования)
- ActivityWatch (https://activitywatch.net/)

### macOS
- Homebrew (https://brew.sh/)
- Python 3.10+ (установить через brew)
- ActivityWatch

### Linux (Ubuntu/Debian)
- Python 3.10+
- pip (обычно идет с Python)
- ActivityWatch

## Шаг 1: Установка ActivityWatch

### Windows
1. Скачайте установщик: https://activitywatch.net/
2. Запустите установщик
3. Откройте PowerShell и запустите aw-server:
   ```powershell
   aw-server
   ```
4. Оставьте окно открытым или добавьте в задачи планировщика

### macOS
```bash
brew install activitywatch
aw-server
```

### Linux (Ubuntu/Debian)
```bash
# Если доступен в репозитории
sudo apt install activitywatch

# Или скачать с сайта
# https://activitywatch.net/

aw-server
```

## Шаг 2: Проверка ActivityWatch

Откройте браузер и перейдите на http://localhost:5600 - должен видеться интерфейс ActivityWatch.

## Шаг 3: Установка FocusPilot

### 1. Клонирование/загрузка проекта

**Если у вас есть Git:**
```bash
git clone https://github.com/your-repo/focuspilot.git
cd focuspilot
```

**Или просто скачайте ZIP и распакуйте:**
```bash
cd FocusPilot
```

### 2. Создание виртуального окружения

**Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Убедитесь, что видите префикс `(venv)` в начале строки команд.**

### 3. Обновление pip

```bash
pip install --upgrade pip
```

### 4. Установка зависимостей

```bash
pip install -r requirements.txt
```

Установка занимает 2-5 минут.

## Шаг 4: Первый запуск

### Проверка установки

Убедитесь, что ActivityWatch запущен, и выполните:

```bash
python main.py
```

Приложение должно вывести:
```
============================================================
FocusPilot v1.0 - Starting...
============================================================
...
ActivityWatch server is available
...
FocusPilot initialized successfully
```

## Варианты запуска

### 1. Фоновый режим (трей иконка)

```bash
python main.py
```

Приложение работает в системном трее. Кликните иконку для доступа к меню.

### 2. С графическим интерфейсом

```bash
python main.py --qt
```

Откроется главное окно с вкладками для плана, статистики и управления.

### 3. Только обучение моделей

```bash
# Однократное обучение (для проверки)
python train_nightly.py --once

# Ежедневное расписание (обучение в 2:00 AM)
python train_nightly.py
```

## Первая сессия

### 1. Ввод плана
- Откройте главное окно (через трей меню или `--qt`)
- Перейдите на вкладку "Daily Plan"
- Введите ваш дневной план:
  ```
  9:00-10:00 Work on implementation
  10:00-10:15 Coffee break
  10:15-12:00 Code review meeting
  12:00-13:00 Lunch
  13:00-15:00 Coding
  ```
- Нажмите "Save Plan"

### 2. Запуск мониторинга
- Перейдите на вкладку "Current Status"
- Нажмите "Start Monitoring"
- Приложение начнет отслеживать вашу активность

### 3. Просмотр статистики
- Перейдите на вкладку "Statistics"
- Статистика обновляется в реальном времени

## Проблемы и решения

### Ошибка: "ActivityWatch server is not available"

**Решение:**
1. Убедитесь, что aw-server запущен
2. Проверьте http://localhost:5600 в браузере
3. Перезагрузите aw-server

### Ошибка: "ModuleNotFoundError: No module named 'PyQt5'"

**Решение:**
```bash
# Убедитесь, что активирована вирт. окружение
# Переустановите зависимости
pip install -r requirements.txt --force-reinstall
```

### Приложение заходит в фоновый режим и недоступно

**Решение:**
- Ищите иконку FocusPilot в системном трее (правый нижний угол)
- На Windows: проверьте "Hidden items" в трее
- На macOS: проверьте меню в верхней правой части

### Уведомления не работают

**Решение:**
- Windows: проверьте параметры уведомлений в настройках
- macOS: разрешите уведомления для Python в System Preferences
- Linux: убедитесь, что установлен notify-send (или похожий)

## Сбор исторических данных

Для лучшей работы ML моделей нужны исторические данные:

1. **Запустите ActivityWatch** на 5-7 дней
2. **Работайте как обычно** - приложение будет собирать данные
3. **Пометьте** некоторую активность в базе (опционально)
4. **Запустите обучение:**
   ```bash
   python train_nightly.py --once
   ```

После обучения классификатор будет более точным.

## Продвинутые настройки

### Изменение интервала мониторинга

В `core/coordinator.py`:
```python
def __init__(self, poll_interval: float = 2.0, ...):
    # Измените 2.0 на нужный интервал в секундах
```

### Изменение порога отвлечения

В `core/coordinator.py` метод `_check_for_distraction`:
```python
if distraction_duration >= 2:  # Измените 2 на нужное в минутах
```

### Изменение часа ночного обучения

В `train_nightly.py`:
```python
run_scheduled(hour=2, minute=0)  # Измените час
```

## Автозапуск приложения

### Windows

1. Нажмите `Win+R` и введите `shell:startup`
2. Создайте батник `start_focuspilot.bat`:
   ```batch
   @echo off
   cd "C:\Users\YourUsername\Desktop\FocusPilot"
   venv\Scripts\activate.bat
   python main.py
   ```
3. Сохраните в папке Startup

### macOS

Создайте `~/Library/LaunchAgents/com.focuspilot.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.focuspilot.main</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/FocusPilot/main.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
```

### Linux (systemd)

Создайте `/etc/systemd/user/focuspilot.service`:
```ini
[Unit]
Description=FocusPilot Daily Plan Controller
After=network.target

[Service]
Type=simple
ExecStart=/home/username/FocusPilot/venv/bin/python /home/username/FocusPilot/main.py
Restart=on-failure

[Install]
WantedBy=default.target
```

Затем:
```bash
systemctl --user enable focuspilot
systemctl --user start focuspilot
```

## Удаление

### Очистка

```bash
# Удаление виртуального окружения
rm -rf venv  # Linux/macOS
rmdir /s venv  # Windows

# Удаление базы данных (если нужно)
rm focuspilot.db

# Удаление логов
rm focuspilot.log
```

### Полное удаление

```bash
# Удалите всю папку FocusPilot
rm -rf FocusPilot  # Linux/macOS
rmdir /s FocusPilot  # Windows
```

## Дополнительная информация

- **Документация ActivityWatch**: https://docs.activitywatch.net/
- **scikit-learn документация**: https://scikit-learn.org/
- **PyQt5 документация**: https://pypi.org/project/PyQt5/

## Получение помощи

Если возникли проблемы:

1. Проверьте логи в `focuspilot.log`
2. Убедитесь, что ActivityWatch запущен
3. Попробуйте переустановить зависимости
4. Удалите `focuspilot.db` и `models/` для полного сброса

---

**Версия**: 1.0  
**Последнее обновление**: 2024
