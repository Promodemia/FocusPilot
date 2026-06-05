"""
FocusPilot - Main Entry Point
Десктоп приложение для контроля плана дня с использованием ActivityWatch
"""

import logging
import sys
import os
import time
from datetime import datetime
from typing import Optional

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('focuspilot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Импорты приложения
from integration.aw_provider import AWDataProvider
from core.coordinator import ActivityCoordinator
from storage.db import DatabaseManager

try:
    from gui.tray_icon import TrayIconManager
except ImportError:
    TrayIconManager = None

try:
    from gui.notifications import NotificationManager
except ImportError:
    NotificationManager = None


class FocusPilotApplication:
    """Главный класс приложения"""
    
    def __init__(self):
        """Инициализация приложения"""
        self.coordinator: Optional[ActivityCoordinator] = None
        self.main_window: Optional[MainWindow] = None
        self.tray_icon: Optional[TrayIconManager] = None
        self.notification_manager: Optional[NotificationManager] = None
        self.db_manager: Optional[DatabaseManager] = None
    
    def check_aw_server(self) -> bool:
        """
        Проверка наличия ActivityWatch сервера
        
        Returns:
            True если сервер доступен
        """
        logger.info("Checking ActivityWatch server...")
        aw_provider = AWDataProvider()
        
        if not aw_provider.is_connected():
            logger.error(
                "ActivityWatch server is not running!\n\n"
                "Please install and start ActivityWatch:\n"
                "1. Download from https://activitywatch.net/\n"
                "2. Install the application\n"
                "3. Start 'aw-server' in the background\n\n"
                "Alternatively, install via package manager:\n"
                "  Windows: choco install activitywatch\n"
                "  macOS: brew install activitywatch\n"
                "  Linux: sudo apt install activitywatch (if available)\n"
            )
            return False
        
        logger.info("ActivityWatch server is available")
        return True
    
    def initialize(self) -> bool:
        """
        Инициализация приложения
        
        Returns:
            True если инициализация успешна
        """
        try:
            logger.info("=" * 60)
            logger.info("FocusPilot v1.0 - Starting...")
            logger.info("=" * 60)
            
            # Проверяем ActivityWatch
            if not self.check_aw_server():
                return False
            
            # Инициализируем компоненты
            self.db_manager = DatabaseManager()
            logger.info("Database initialized")
            
            self.coordinator = ActivityCoordinator()
            logger.info("Coordinator initialized")
            
            # Настраиваем уведомления
            if NotificationManager is not None:
                self.notification_manager = NotificationManager()
                self.coordinator.notification_callback = self.notification_manager.show_distraction_alert
            else:
                self.notification_manager = None
                logger.warning("NotificationManager unavailable, notifications disabled")
            
            # Создаем трей иконку, если доступна
            if TrayIconManager is not None:
                self.tray_icon = TrayIconManager(on_quit=self.shutdown)
            else:
                self.tray_icon = None
                logger.warning("TrayIconManager unavailable, tray icon disabled")
            
            # Создаем главное окно (но не показываем автоматически)
            # Это можно сделать через трей меню
            
            logger.info("FocusPilot initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize FocusPilot: {e}", exc_info=True)
            return False
    
    def run(self) -> None:
        """Запуск приложения"""
        if not self.initialize():
            logger.error("Could not initialize FocusPilot. Exiting.")
            sys.exit(1)
        
        try:
            if self.tray_icon:
                logger.info("Starting tray icon...")
                self.tray_icon.run()
            else:
                # Fallback: запускаем мониторинг в фоновом режиме без трея
                logger.info("Running in background monitoring mode (no tray icon)")
                if self.coordinator:
                    self.coordinator.start_coordinator()
                    logger.info("Monitoring started. Press Ctrl+C to stop.")
                    while True:
                        time.sleep(1)
        
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        
        except Exception as e:
            logger.error(f"Error running FocusPilot: {e}", exc_info=True)
        
        finally:
            self.shutdown()
    
    def run_with_qt_window(self) -> None:
        """Запуск приложения с главным окном (Tkinter)"""
        if not self.initialize():
            logger.error("Could not initialize FocusPilot. Exiting.")
            sys.exit(1)
        
        try:
            from gui.main_window import MainWindow
            
            # Создаем главное окно на Tkinter
            logger.info("Creating Tkinter window...")
            self.main_window = MainWindow(coordinator=self.coordinator, config={
                'distraction_threshold_seconds': 120,
                'enable_notifications': True
            })
            
            # Интегрируем уведомления с главным окном
            if self.notification_manager and self.main_window:
                self.coordinator.notification_callback = (
                    self.notification_manager.show_distraction_alert
                )
            
            # Запускаем координатор в фоновом потоке
            if self.coordinator:
                self.coordinator.start_coordinator()
                logger.info("Coordinator started in background")
            
            logger.info("Tkinter window created and running...")
            self.main_window.mainloop()
        
        except Exception as e:
            logger.error(f"Error running Tkinter window: {e}", exc_info=True)
            self.run()
    
    def shutdown(self) -> None:
        """Завершение приложения"""
        logger.info("Shutting down FocusPilot...")
        
        try:
            if self.coordinator and self.coordinator.is_running:
                self.coordinator.stop_coordinator()
                logger.info("Coordinator stopped")
            
            if self.tray_icon:
                self.tray_icon.stop()
                logger.info("Tray icon stopped")
            
            logger.info("=" * 60)
            logger.info("FocusPilot stopped successfully")
            logger.info("=" * 60)
        
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


def main():
    """Точка входа приложения"""
    # Определяем режим запуска (Qt окно или только трей)
    use_qt = "--qt" in sys.argv or "--window" in sys.argv
    
    app = FocusPilotApplication()
    
    if use_qt:
        app.run_with_qt_window()
    else:
        # Запуск в фоновом режиме с трей иконкой
        # Главное окно можно открыть через трей меню
        print("\n" + "=" * 60)
        print("FocusPilot started in background mode")
        print("Look for the FocusPilot icon in your system tray")
        print("=" * 60 + "\n")
        
        app.run()


if __name__ == "__main__":
    main()
